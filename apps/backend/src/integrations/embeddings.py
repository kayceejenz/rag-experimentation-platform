import time
import math
import httpx

class GeminiEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-2",
        dimensions: int = 768,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        batch_size: int = 100,
        timeout_seconds: float = 120,
        max_retries: int = 4,
    ) -> None:
        self.api_key = api_key
        self.model = model.removeprefix("models/")
        self.dimensions = dimensions
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        unique_texts = list(dict.fromkeys(texts))
        vectors_by_text: dict[str, list[float]] = {}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            for start in range(0, len(unique_texts), self.batch_size):
                batch = unique_texts[start : start + self.batch_size]
                vectors = self._embed_batch(client, batch)
                if len(vectors) != len(batch):
                    raise ValueError("Gemini returned the wrong number of embedding vectors")
                
                vectors_by_text.update(zip(batch, vectors, strict=True))
        return [vectors_by_text[text] for text in texts]

    def _embed_batch(self, client: httpx.Client, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/models/{self.model}:batchEmbedContents"
        payload = {
            "requests": [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": self.dimensions,
                }
                for text in texts
            ]
        }
        for attempt in range(self.max_retries + 1):
            response = client.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=payload,
            )
            if response.status_code == 429 and self._is_depleted_billing(response):
                raise RuntimeError(
                    "Gemini embedding quota is unavailable because the project's prepayment "
                    "credits are depleted; update the project in Google AI Studio"
                )
                
            if response.status_code != 429 and response.status_code < 500:
                response.raise_for_status()
                return [self._normalize(item["values"]) for item in response.json()["embeddings"]]
            
            if attempt == self.max_retries:
                response.raise_for_status()
            retry_after = response.headers.get("retry-after")
            delay = float(retry_after) if retry_after else min(2**attempt, 16)
            time.sleep(delay)
        raise RuntimeError("Gemini embedding request failed")

    @staticmethod
    def _normalize(vectors: list[float]) -> list[float]:
        norm = math.sqrt(sum(v*v for v in vectors))
        return [ v/norm for v in vectors] if norm else vectors
    
    @staticmethod
    def _is_depleted_billing(response: httpx.Response) -> bool:
        try:
            message = response.json().get("error", {}).get("message", "")
        except ValueError:
            return False
        return "prepayment credits are depleted" in message.lower()
