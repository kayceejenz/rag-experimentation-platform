from collections import OrderedDict
from collections.abc import Awaitable, Callable
import asyncio
import inspect
import time
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from integrations.database import async_db_connection

from modules.chats.models.retrieval_model import RetrievedChunk


class QueryEmbeddingCache:
    """Run-scoped, model-aware cache with single-flight embedding generation."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str, int, str], list[float]] = {}
        self._locks: dict[tuple[str, str, int, str], asyncio.Lock] = {}

    async def get_or_create(
        self,
        key: tuple[str, str, int, str],
        factory: Callable[[], Awaitable[list[float]]],
    ) -> tuple[list[float], bool]:
        cached = self._values.get(key)
        if cached is not None:
            return cached, True
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._values.get(key)
            if cached is not None:
                return cached, True
            value = await factory()
            self._values[key] = value
            self._locks.pop(key, None)
            return value, False


class PgVectorKnowledgeSearch:
    def __init__(
        self,
        database_url: str,
        embedder,
        provider: str,
        model_name: str,
        candidate_limit: int = 16,
        min_score: float = 0.25,
        cache_size: int = 128,
        specification_id=None,
        embedding_model_id=None,
        dimensions: int | None = None,
        distance_metric: str = "cosine",
        query_embedding_cache: QueryEmbeddingCache | None = None,
    ) -> None:
        self.database_url = database_url
        self.embedder = embedder
        self.provider = provider
        self.model_name = model_name
        self.candidate_limit = candidate_limit
        self.min_score = min_score
        self.cache_size = cache_size
        self.specification_id = specification_id
        self.embedding_model_id = (
            UUID(str(embedding_model_id)) if embedding_model_id else None
        )
        self.dimensions = int(dimensions or getattr(embedder, "dimensions", 0))
        self.distance_metric = distance_metric
        self.query_embedding_cache = query_embedding_cache
        self._query_cache: OrderedDict[str, list[float]] = OrderedDict()

    async def search(
        self, knowledge_base_id, query: str, limit: int = 8, telemetry: dict | None = None
    ) -> list[RetrievedChunk]:
        embedding_started = time.perf_counter()
        vector = await self._query_vector(query, telemetry)
        if telemetry is not None:
            telemetry["embedding_latency"] = (
                time.perf_counter() - embedding_started
            ) * 1000
        vector_literal = "[" + ",".join(str(float(value)) for value in vector) + "]"
        distance_expression, score_expression, model_filter, model_parameters = (
            self._search_expression()
        )
        search_started = time.perf_counter()
        async with async_db_connection(self.database_url, row_factory=dict_row) as db:
            await db.execute("set local hnsw.iterative_scan = strict_order")
            cur = await db.execute(
                "with candidates as (select c.id chunk_id,c.source_id,c.source_version_id,"
                "c.position,s.display_name source_filename,c.content,c.page_from,c.metadata,"
                f"{score_expression} vector_score,"
                "ts_rank_cd(c.search_vector,plainto_tsquery('english',%s)) lexical_score "
                "from ragapp.chunks c join ragapp.sources s on s.id=c.source_id "
                "join ragapp.source_versions sv on sv.id=c.source_version_id "
                "join ragapp.chunk_embeddings ce on ce.chunk_id=c.id "
                "join ragapp.embedding_models em on em.id=ce.embedding_model_id "
                "where c.knowledge_base_id=%s "
                "and (%s::uuid is not null or s.deleted_at is null) "
                "and (%s::uuid is null or c.specification_id=%s) "
                "and (%s::uuid is not null or not exists("
                "select 1 from ragapp.source_versions newer "
                "where newer.source_id=sv.source_id and newer.version>sv.version)) "
                f"and {model_filter} "
                f"order by {distance_expression} limit %s) "
                "select *,0.8*vector_score+0.2*least(lexical_score*4,1) score "
                "from candidates where vector_score >= %s "
                "order by score desc limit %s",
                (
                    vector_literal,
                    query,
                    knowledge_base_id,
                    self.specification_id,
                    self.specification_id,
                    self.specification_id,
                    self.specification_id,
                    *model_parameters,
                    vector_literal,
                    self.candidate_limit,
                    self.min_score,
                    limit,
                ),
            )
            rows = await cur.fetchall()
            rows = await self._expand_neighbors(db, rows)
        if telemetry is not None:
            telemetry["vector_search_latency"] = (
                time.perf_counter() - search_started
            ) * 1000

        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                source_id=row["source_id"],
                source_filename=row["source_filename"],
                text=row["content"],
                score=float(row["score"]),
                page_number=row["page_from"],
                element_ids=tuple((row["metadata"] or {}).get("element_ids", [])),
                coordinates=(),
                metadata=dict(row["metadata"] or {}),
            )
            for row in rows
        ]

    def _search_expression(self):
        operator = {
            "cosine": "<=>",
            "l2": "<->",
            "inner_product": "<#>",
        }.get(self.distance_metric)
        if operator is None:
            raise ValueError(f"Unsupported vector distance metric: {self.distance_metric}")
        if self.embedding_model_id is None:
            distance = f"ce.embedding {operator} %s::vector"
            return (
                distance,
                self._score_expression(distance),
                "em.provider=%s and em.model_name=%s",
                (self.provider, self.model_name),
            )
        if self.specification_id is None:
            raise ValueError("An index specification is required for indexed retrieval")
        if not 1 <= self.dimensions <= 4000:
            raise ValueError("Indexed embedding dimensions must be between 1 and 4000")
        indexed_type = "vector" if self.dimensions <= 2000 else "halfvec"
        expression = (
            f"ce.embedding::{indexed_type}({self.dimensions}) "
            f"{operator} %s::{indexed_type}({self.dimensions})"
        )
        model_id = str(self.embedding_model_id)
        specification_id = str(UUID(str(self.specification_id)))
        return (
            expression,
            self._score_expression(expression),
            f"ce.embedding_model_id='{model_id}'::uuid "
            f"and ce.specification_id='{specification_id}'::uuid",
            (),
        )

    def _score_expression(self, distance_expression):
        if self.distance_metric == "cosine":
            # pgvector cosine distance spans 0..2. Convert cosine similarity's
            # -1..1 range into the public retrieval score contract of 0..1.
            return f"1-(({distance_expression})/2)"
        if self.distance_metric == "inner_product":
            return f"-({distance_expression})"
        return f"1/(1+({distance_expression}))"

    @staticmethod
    async def _expand_neighbors(db: AsyncConnection, seeds: list[dict]):
        if not seeds:
            return seeds
        
        neighbor_threshold = 0.60
        expandable = [row for row in seeds if float(row["score"]) >= neighbor_threshold]
        non_expandable = [row for row in seeds if float(row["score"]) < neighbor_threshold]
        seed_ids = [row["chunk_id"] for row in expandable]
        seed_scores = {row["chunk_id"]: float(row["score"]) for row in expandable}

        if not seed_ids:
            return seeds
        
        cur = await db.execute(
            "with seeds as (select * from unnest(%s::uuid[]) with ordinality "
            "as seed(chunk_id,seed_rank)), expanded as (select distinct on(c.id) "
            "c.id chunk_id,c.source_id,s.display_name source_filename,c.content,"
            "c.page_from,c.metadata,seeds.chunk_id seed_id,seeds.seed_rank,c.position "
            "from seeds join ragapp.chunks root on root.id=seeds.chunk_id "
            "join ragapp.chunks c on c.source_version_id=root.source_version_id "
            "and c.position between root.position-1 and root.position+1 "
            "and c.specification_id is not distinct from root.specification_id "
            "join ragapp.sources s on s.id=c.source_id "
            "order by c.id,seeds.seed_rank) select * from expanded "
            "order by seed_rank,position",
            (seed_ids,),
        )
        rows = await cur.fetchall()
        for row in rows:
            row["score"] = seed_scores[row["seed_id"]]
        seen = {row["chunk_id"] for row in rows}
        for row in non_expandable:
            if row["chunk_id"] not in seen:
                rows.append(row)
                seen.add(row["chunk_id"])
        return rows

    async def _query_vector(self, query: str, telemetry: dict | None = None) -> list[float]:
        key = " ".join(query.lower().split())
        run_key = (self.provider, self.model_name, self.dimensions, key)
        if self.query_embedding_cache is not None:
            vector, cache_hit = await self.query_embedding_cache.get_or_create(
                run_key, lambda: self._embed_query(query)
            )
            if telemetry is not None:
                telemetry["embedding_cache_hit"] = cache_hit
            return vector
        cached = self._query_cache.get(key)
        if cached is not None:
            self._query_cache.move_to_end(key)
            if telemetry is not None:
                telemetry["embedding_cache_hit"] = True
            return cached

        vector = await self._embed_query(query)
        if telemetry is not None:
            telemetry["embedding_cache_hit"] = False
        self._query_cache[key] = vector
        self._query_cache.move_to_end(key)
        while len(self._query_cache) > self.cache_size:
            self._query_cache.popitem(last=False)
        return vector

    async def _embed_query(self, query: str) -> list[float]:
        embed_async = getattr(self.embedder, "embed_async", None)
        if embed_async is not None:
            result = await embed_async([query])
        elif inspect.iscoroutinefunction(self.embedder.embed):
            result = await self.embedder.embed([query])
        else:
            result = await asyncio.to_thread(self.embedder.embed, [query])
        return result[0]
