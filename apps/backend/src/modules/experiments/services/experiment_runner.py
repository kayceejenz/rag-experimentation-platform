import asyncio
import json
import socket
import time
from statistics import mean

from integrations.embeddings import GeminiEmbedder
from integrations.gemini_chat import GeminiChatModel
from integrations.rate_limit import AsyncRateLimiter
from integrations.retrieval_store import PgVectorKnowledgeSearch, QueryEmbeddingCache
from modules.experiments.repos.run_repository import ExperimentRunRepository


def render(template, values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value or ""))
    return template


def parse_score(text):
    try:
        value = json.loads(
            text.strip().removeprefix("```json").removesuffix("```").strip()
        )
        return float(value["score"]), value.get("reason", "")
    except Exception:
        return None, text[:500]


def bounded_context(chunks, max_chars):
    parts = []
    rows = []
    remaining = max_chars
    for index, chunk in enumerate(chunks):
        prefix = f"[{index + 1}] {chunk.source_filename}: "
        separator = "\n\n" if parts else ""
        available = remaining - len(separator) - len(prefix)
        if available <= 0:
            break
        text = chunk.text
        if len(text) > available:
            text = text[:available].rstrip()
        rendered = f"{separator}{prefix}{text}"
        parts.append(rendered)
        rows.append(
            {
                "chunk_id": str(chunk.chunk_id),
                "source": chunk.source_filename,
                "text": text,
                "score": chunk.score,
                "page": chunk.page_number,
            }
        )
        remaining -= len(rendered)
        if len(text) < len(chunk.text):
            break
    return "".join(parts), rows


class RateLimitedEmbedder:
    def __init__(self, embedder, limiter):
        self.embedder = embedder
        self.limiter = limiter
        self.dimensions = embedder.dimensions

    async def embed(self, texts):
        async with self.limiter.limit():
            return await asyncio.to_thread(self.embedder.embed, texts)


async def provider_call(limiter, operation, *args):
    async with limiter.limit() as wait_ms:
        result = await asyncio.to_thread(operation, *args)
    return result, wait_ms


async def heartbeat(repo, run_id, worker_id, interval):
    while True:
        await asyncio.sleep(interval)
        await asyncio.to_thread(repo.heartbeat, run_id, worker_id)


async def run_once(config):
    repo = ExperimentRunRepository(config.database_url)
    worker_id = socket.gethostname()
    run = await asyncio.to_thread(
        repo.claim, worker_id, config.experiment_run_lease_seconds
    )
    if not run:
        return False
    heartbeat_task = asyncio.create_task(
        heartbeat(
            repo,
            run["id"],
            worker_id,
            max(20, config.experiment_run_lease_seconds // 3),
        )
    )
    try:
        payload, variants = await asyncio.to_thread(repo.payload, run["id"])
        query_embedding_cache = QueryEmbeddingCache()
        provider_limiter = AsyncRateLimiter(
            config.experiment_provider_max_concurrency,
            config.experiment_provider_requests_per_minute,
        )
        variant_semaphore = asyncio.Semaphore(config.experiment_variant_concurrency)
        case_semaphore = asyncio.Semaphore(config.experiment_case_concurrency)
        evaluator_semaphore = asyncio.Semaphore(config.experiment_evaluator_concurrency)

        async def execute_variant(variant):
            if variant["variant_run_status"] == "completed":
                return None
            async with variant_semaphore:
                return await _run_variant(
                    config,
                    repo,
                    payload,
                    variant,
                    query_embedding_cache,
                    provider_limiter,
                    case_semaphore,
                    evaluator_semaphore,
                )

        variant_results = await asyncio.gather(
            *(execute_variant(variant) for variant in variants),
            return_exceptions=True,
        )
        errors = [str(result) for result in variant_results if result]
        await asyncio.to_thread(
            repo.finish, run["id"], "; ".join(errors)[:2000] if errors else None
        )
    except Exception as error:
        await asyncio.to_thread(repo.finish, run["id"], str(error)[:2000])
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
    return True


async def _run_variant(
    config,
    repo,
    run,
    variant,
    query_embedding_cache,
    provider_limiter,
    case_semaphore,
    evaluator_semaphore,
):
    await asyncio.to_thread(repo.start_variant, variant["variant_run_id"])
    try:
        idx = variant["index_configuration"]
        embedding = idx["embedding"]
        generation = variant["generation_configuration"]
        retrieval = variant["retrieval_configuration"]
        knowledge_base_id = variant.get("knowledge_base_id")
        if not knowledge_base_id:
            raise ValueError(
                "The selected index has no resolvable knowledge-base scope"
            )
        embedder = RateLimitedEmbedder(
            GeminiEmbedder(
                config.embedding_api_key or config.llm_api_key,
                embedding["model"],
                embedding["dimensions"],
                config.gemini_api_url,
                config.embedding_batch_size,
            ),
            provider_limiter,
        )
        search = PgVectorKnowledgeSearch(
            config.database_url,
            embedder,
            embedding["provider"],
            embedding["model"],
            max(16, retrieval["top_k"] * 2),
            retrieval["min_score"],
            specification_id=variant["index_specification_id"],
            embedding_model_id=variant["embedding_model_id"],
            dimensions=embedding["dimensions"],
            distance_metric=variant["embedding_distance_metric"],
            query_embedding_cache=query_embedding_cache,
        )
        model = GeminiChatModel(
            config.llm_api_key or config.embedding_api_key,
            generation["model"],
            config.gemini_api_url,
            max_output_tokens=generation["max_output_tokens"],
        )

        completed = await asyncio.to_thread(
            repo.completed_cases, variant["variant_run_id"]
        )
        completed_ids = {str(row["case_id"]) for row in completed}
        all_metrics = [row["metrics"] for row in completed]

        async def execute_case(position, case):
            if str(case["case_id"]) in completed_ids:
                return None
            async with case_semaphore:
                return await _run_case(
                    config,
                    repo,
                    run,
                    variant,
                    case,
                    position,
                    search,
                    model,
                    provider_limiter,
                    evaluator_semaphore,
                )

        results = await asyncio.gather(
            *(execute_case(position, case) for position, case in enumerate(run["content"])),
            return_exceptions=True,
        )
        errors = []
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result)[:500])
            elif result is not None:
                all_metrics.append(result)

        aggregate = {}
        for metric in run["metrics"]:
            values = [
                m[metric]["score"] if isinstance(m.get(metric), dict) else m.get(metric)
                for m in all_metrics
                if m.get(metric) is not None
            ]
            if values:
                aggregate[metric] = mean(values)
        error = "; ".join(errors)[:2000] if errors else None
        await asyncio.to_thread(
            repo.finish_variant, variant["variant_run_id"], aggregate, error
        )
        return error
    except Exception as error:
        await asyncio.to_thread(
            repo.finish_variant,
            variant["variant_run_id"],
            {},
            str(error)[:2000],
        )
        return str(error)[:2000]


async def _run_case(
    config,
    repo,
    run,
    variant,
    case,
    position,
    search,
    model,
    provider_limiter,
    evaluator_semaphore,
):
    case_started = time.perf_counter()
    retrieval_started = time.perf_counter()
    retrieval_telemetry = {}
    retrieval = variant["retrieval_configuration"]
    chunks = await search.search(
        variant["knowledge_base_id"],
        case["question"],
        retrieval["top_k"],
        telemetry=retrieval_telemetry,
    )
    retrieval_ms = (time.perf_counter() - retrieval_started) * 1000

    context_started = time.perf_counter()
    context, context_rows = bounded_context(chunks, config.experiment_max_context_chars)
    context_ms = (time.perf_counter() - context_started) * 1000
    values = {
        "question": case["question"],
        "context": context,
        "reference_answer": case.get("reference_answer"),
        "answer": "",
    }
    prompt = render(variant["rag_template"], values)

    generation_started = time.perf_counter()
    (answer, usage), generation_wait_ms = await provider_call(
        provider_limiter,
        model.generate_configured,
        variant["system_template"],
        prompt,
        variant["generation_configuration"]["temperature"],
        variant["generation_configuration"]["max_output_tokens"],
    )
    generation_ms = (time.perf_counter() - generation_started) * 1000
    values["answer"] = answer

    async def evaluate(metric, template):
        async with evaluator_semaphore:
            started = time.perf_counter()
            (judged, _), wait_ms = await provider_call(
                provider_limiter,
                model.generate_configured,
                "You are an impartial evaluation judge. Return the requested JSON only.",
                render(template, values),
                0,
                1024,
            )
            score, reason = parse_score(judged)
            return metric, {
                "score": score,
                "reason": reason,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "provider_queue_latency_ms": wait_ms,
            }

    evaluation_started = time.perf_counter()
    evaluations = await asyncio.gather(
        *(evaluate(metric, template) for metric, template in variant["evaluators"].items())
    )
    evaluation_ms = (time.perf_counter() - evaluation_started) * 1000
    metrics = {
        "embedding_latency": retrieval_telemetry.get("embedding_latency", 0.0),
        "embedding_cache_hit": retrieval_telemetry.get("embedding_cache_hit", False),
        "vector_search_latency": retrieval_telemetry.get("vector_search_latency", 0.0),
        "retrieval_latency": retrieval_ms,
        "context_assembly_latency": context_ms,
        "generation_latency": generation_ms,
        "evaluation_latency": evaluation_ms,
        "provider_queue_latency": generation_wait_ms
        + sum(value[1]["provider_queue_latency_ms"] for value in evaluations),
        "token_count": usage["total_tokens"],
        "estimated_cost": 0.0,
    }
    metrics.update(evaluations)
    metrics["total_latency"] = (time.perf_counter() - case_started) * 1000
    await asyncio.to_thread(
        repo.save_case,
        variant["variant_run_id"],
        case,
        position,
        context_rows,
        answer,
        metrics,
    )
    return metrics
