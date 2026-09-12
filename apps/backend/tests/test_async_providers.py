import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from integrations.embeddings import GeminiEmbedder
from integrations.gemini_chat import GeminiChatModel


class AsyncProviderTests(unittest.IsolatedAsyncioTestCase):
    def test_assistant_request_preserves_configured_system_prompt(self) -> None:
        model = GeminiChatModel(
            "key",
            "generation-model",
            system_prompt="Configured assistant behaviour",
            rag_prompt="Context: {{context}}\nQuestion: {{question}}",
        )

        request = model._request("What happened?", "[1] Evidence", [])

        self.assertEqual(
            "Configured assistant behaviour",
            request["systemInstruction"]["parts"][0]["text"],
        )
        rendered = request["contents"][-1]["parts"][0]["text"]
        self.assertIn("Context: [1] Evidence", rendered)
        self.assertIn("Do not cite every retrieved passage", rendered)
        self.assertIn("never output empty brackets []", rendered)
        self.assertEqual(
            {"thinkingLevel": "low", "includeThoughts": True},
            request["generationConfig"]["thinkingConfig"],
        )

    async def test_embedding_uses_async_http_client(self) -> None:
        async_client = MagicMock()
        async_client.post = AsyncMock(
            return_value=httpx.Response(
                200,
                json={"embeddings": [{"values": [3.0, 4.0]}]},
                request=httpx.Request("POST", "https://example.test"),
            )
        )
        sync_client = MagicMock()
        embedder = GeminiEmbedder(
            "key",
            "embedding-model",
            dimensions=2,
            client=sync_client,
            async_client=async_client,
        )

        vectors = await embedder.embed_async(["question"])

        self.assertEqual([[0.6, 0.8]], vectors)
        async_client.post.assert_awaited_once()
        sync_client.post.assert_not_called()

    async def test_generation_uses_async_http_client(self) -> None:
        async_client = MagicMock()
        async_client.post = AsyncMock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": "Grounded answer"}]}}
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 10,
                        "candidatesTokenCount": 3,
                        "totalTokenCount": 13,
                    },
                },
                request=httpx.Request("POST", "https://example.test"),
            )
        )
        model = GeminiChatModel(
            "key",
            "generation-model",
            async_client=async_client,
        )

        answer, usage = await model.generate_configured(
            "system", "question", 0.1, 100
        )

        self.assertEqual("Grounded answer", answer)
        self.assertEqual(13, usage["total_tokens"])
        async_client.post.assert_awaited_once()

    async def test_generation_retries_without_blocking_the_event_loop(self) -> None:
        request = httpx.Request("POST", "https://example.test")
        async_client = MagicMock()
        async_client.post = AsyncMock(
            side_effect=[
                httpx.Response(503, request=request),
                httpx.Response(
                    200,
                    json={
                        "candidates": [
                            {"content": {"parts": [{"text": "Recovered"}]}}
                        ]
                    },
                    request=request,
                ),
            ]
        )
        model = GeminiChatModel(
            "key", "generation-model", max_retries=1, async_client=async_client
        )

        with patch("integrations.gemini_chat.asyncio.sleep", new_callable=AsyncMock) as sleep:
            answer = await model.generate("question", "context", [])

        self.assertEqual("Recovered", answer)
        self.assertEqual(2, async_client.post.await_count)
        sleep.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
