import asyncio
import unittest
from uuid import uuid4

from integrations.rate_limit import AsyncRateLimiter
from integrations.retrieval_store import PgVectorKnowledgeSearch, QueryEmbeddingCache
from modules.chats.models.retrieval_model import RetrievedChunk
from modules.experiments.services.experiment_runner import bounded_context


class Embedder:
    def __init__(self):
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return [[0.1, 0.2, 0.3] for _ in texts]


def chunk(text):
    return RetrievedChunk(
        chunk_id=uuid4(),
        source_id=uuid4(),
        source_filename="guide.txt",
        text=text,
        score=0.9,
        page_number=1,
        element_ids=(),
        coordinates=(),
        metadata={},
    )


class ContextBudgetTests(unittest.TestCase):
    def test_context_and_recorded_rows_respect_the_same_budget(self):
        context, rows = bounded_context([chunk("a" * 100), chunk("b" * 100)], 50)

        self.assertLessEqual(len(context), 50)
        self.assertEqual(1, len(rows))
        self.assertIn(rows[0]["text"], context)
        self.assertLess(len(rows[0]["text"]), 100)


class QueryEmbeddingCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_is_shared_within_run_and_scoped_by_model_configuration(self):
        embedder = Embedder()
        cache = QueryEmbeddingCache()
        first = PgVectorKnowledgeSearch(
            "postgresql://unused",
            embedder,
            "gemini",
            "embedding-model",
            dimensions=3,
            query_embedding_cache=cache,
        )
        second = PgVectorKnowledgeSearch(
            "postgresql://unused",
            embedder,
            "gemini",
            "embedding-model",
            dimensions=3,
            query_embedding_cache=cache,
        )
        different_dimensions = PgVectorKnowledgeSearch(
            "postgresql://unused",
            embedder,
            "gemini",
            "embedding-model",
            dimensions=4,
            query_embedding_cache=cache,
        )

        await asyncio.gather(
            first._query_vector("Repeated   question"),
            second._query_vector("repeated question"),
        )
        await different_dimensions._query_vector("repeated question")

        self.assertEqual(2, embedder.calls)


class ProviderRateLimiterTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_concurrency_is_bounded(self):
        limiter = AsyncRateLimiter(max_concurrency=2, requests_per_minute=100)
        active = 0
        peak = 0

        async def request():
            nonlocal active, peak
            async with limiter.limit():
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.01)
                active -= 1

        await asyncio.gather(*(request() for _ in range(6)))

        self.assertEqual(2, peak)
