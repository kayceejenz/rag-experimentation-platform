from collections import OrderedDict
import inspect

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from modules.chats.models.retrieval_model import RetrievedChunk


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
    ) -> None:
        self.database_url = database_url
        self.embedder = embedder
        self.provider = provider
        self.model_name = model_name
        self.candidate_limit = candidate_limit
        self.min_score = min_score
        self.cache_size = cache_size
        self._query_cache: OrderedDict[str, list[float]] = OrderedDict()

    async def search(self, knowledge_base_id, query: str, limit: int = 8) -> list[RetrievedChunk]:
        vector = await self._query_vector(query)
        vector_literal = "[" + ",".join(str(float(value)) for value in vector) + "]"
        async with await AsyncConnection.connect(self.database_url, row_factory=dict_row) as db:
            cur = await db.execute(
                "with candidates as (select c.id chunk_id,c.source_id,c.source_version_id,"
                "c.position,s.display_name source_filename,c.content,c.page_from,c.metadata,"
                "1-(ce.embedding <=> %s::vector) vector_score,"
                "ts_rank_cd(c.search_vector,plainto_tsquery('english',%s)) lexical_score "
                "from ragapp.chunks c join ragapp.sources s on s.id=c.source_id "
                "join ragapp.chunk_embeddings ce on ce.chunk_id=c.id "
                "join ragapp.embedding_models em on em.id=ce.embedding_model_id "
                "where c.knowledge_base_id=%s and s.deleted_at is null "
                "and em.provider=%s and em.model_name=%s "
                "order by ce.embedding <=> %s::vector limit %s) "
                "select *,0.8*vector_score+0.2*least(lexical_score*4,1) score "
                "from candidates where vector_score >= %s "
                "order by score desc limit %s",
                (
                    vector_literal,
                    query,
                    knowledge_base_id,
                    self.provider,
                    self.model_name,
                    vector_literal,
                    self.candidate_limit,
                    self.min_score,
                    limit,
                ),
            )
            rows = await cur.fetchall()
            rows = await self._expand_neighbors(db, rows)

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
            "join ragapp.sources s on s.id=c.source_id and s.deleted_at is null "
            "order by c.id,seeds.seed_rank) select * from expanded "
            "order by seed_rank,position",
            (seed_ids,),
        )
        rows = await cur.fetchall()
        for row in rows:
            row["score"] = seed_scores[row["seed_id"]]
        return rows + non_expandable

    async def _query_vector(self, query: str) -> list[float]:
        key = " ".join(query.lower().split())
        cached = self._query_cache.get(key)
        if cached is not None:
            self._query_cache.move_to_end(key)
            return cached

        res = self.embedder.embed([query])
        if inspect.isawaitable(res):
            res = await res
        vector = res[0]

        self._query_cache[key] = vector
        self._query_cache.move_to_end(key)
        while len(self._query_cache) > self.cache_size:
            self._query_cache.popitem(last=False)
        return vector