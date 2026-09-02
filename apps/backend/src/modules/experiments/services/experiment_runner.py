import json
import socket
import time
from statistics import mean

from integrations.embeddings import GeminiEmbedder
from integrations.gemini_chat import GeminiChatModel
from integrations.retrieval_store import PgVectorKnowledgeSearch
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


def run_once(config):
    repo = ExperimentRunRepository(config.database_url)
    run = repo.claim(socket.gethostname())
    if not run:
        return False
    try:
        payload, variants = repo.payload(run["id"])
        for variant in variants:
            _run_variant(config, repo, payload, variant)
        repo.finish(run["id"])
    except Exception as error:
        repo.finish(run["id"], str(error)[:2000])
    return True


def _run_variant(config, repo, run, variant):
    repo.start_variant(variant["variant_run_id"])
    all_metrics = []
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
        embedder = GeminiEmbedder(
            config.embedding_api_key or config.llm_api_key,
            embedding["model"],
            embedding["dimensions"],
            config.gemini_api_url,
            config.embedding_batch_size,
        )
        search = PgVectorKnowledgeSearch(
            config.database_url,
            embedder,
            embedding["provider"],
            embedding["model"],
            max(16, retrieval["top_k"] * 2),
            retrieval["min_score"],
        )
        model = GeminiChatModel(
            config.llm_api_key or config.embedding_api_key,
            generation["model"],
            config.gemini_api_url,
            max_output_tokens=generation["max_output_tokens"],
        )
        import asyncio

        for position, case in enumerate(run["content"]):
            started = time.perf_counter()
            chunks = asyncio.run(
                search.search(knowledge_base_id, case["question"], retrieval["top_k"])
            )
            retrieval_ms = (time.perf_counter() - started) * 1000
            context = "\n\n".join(
                f"[{i + 1}] {c.source_filename}: {c.text}" for i, c in enumerate(chunks)
            )
            values = {
                "question": case["question"],
                "context": context,
                "reference_answer": case.get("reference_answer"),
                "answer": "",
            }
            prompt = render(variant["rag_template"], values)
            generation_started = time.perf_counter()
            answer, usage = model.generate_configured(
                variant["system_template"],
                prompt,
                generation["temperature"],
                generation["max_output_tokens"],
            )
            generation_ms = (time.perf_counter() - generation_started) * 1000
            values["answer"] = answer
            metrics = {
                "retrieval_latency": retrieval_ms,
                "total_latency": retrieval_ms + generation_ms,
                "token_count": usage["total_tokens"],
                "estimated_cost": 0.0,
            }
            for metric, template in variant["evaluators"].items():
                judged, _ = model.generate_configured(
                    "You are an impartial evaluation judge. Return the requested JSON only.",
                    render(template, values),
                    0,
                    1024,
                )
                score, reason = parse_score(judged)
                metrics[metric] = {"score": score, "reason": reason}
            context_rows = [
                {
                    "chunk_id": str(c.chunk_id),
                    "source": c.source_filename,
                    "text": c.text,
                    "score": c.score,
                    "page": c.page_number,
                }
                for c in chunks
            ]
            repo.save_case(
                variant["variant_run_id"], case, position, context_rows, answer, metrics
            )
            all_metrics.append(metrics)
        aggregate = {}
        for metric in run["metrics"]:
            values = [
                m[metric]["score"] if isinstance(m.get(metric), dict) else m.get(metric)
                for m in all_metrics
                if m.get(metric) is not None
            ]
            if values:
                aggregate[metric] = mean(values)
        repo.finish_variant(variant["variant_run_id"], aggregate)
    except Exception as error:
        repo.finish_variant(variant["variant_run_id"], {}, str(error)[:2000])
        raise
