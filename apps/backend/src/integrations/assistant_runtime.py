from integrations.embeddings import GeminiEmbedder
from integrations.gemini_chat import GeminiChatModel
from integrations.retrieval_store import PgVectorKnowledgeSearch


class AssistantRuntimeFactory:
    def __init__(self, settings):
        self.settings = settings

    def create(self, configuration):
        embedding = configuration["embedding"]
        retrieval = configuration["retrieval"]
        generation = configuration["generation"]
        embedder = GeminiEmbedder(
            self.settings.embedding_api_key or self.settings.llm_api_key,
            embedding["model"],
            embedding["dimensions"],
            self.settings.gemini_api_url,
            self.settings.embedding_batch_size,
        )
        search = PgVectorKnowledgeSearch(
            self.settings.database_url,
            embedder,
            embedding["provider"],
            embedding["model"],
            max(16, int(retrieval["top_k"]) * 2),
            float(retrieval["min_score"]),
            specification_id=configuration["index_specification_id"],
            embedding_model_id=configuration["embedding_model_id"],
            dimensions=embedding["dimensions"],
            distance_metric=embedding.get("distance_metric", "cosine"),
        )
        generator = GeminiChatModel(
            self.settings.llm_api_key or self.settings.embedding_api_key,
            generation["model"],
            self.settings.gemini_api_url,
            max_output_tokens=int(generation["max_output_tokens"]),
            system_prompt=configuration["system_prompt"],
            rag_prompt=configuration["rag_prompt"],
            temperature=float(generation["temperature"]),
        )
        return search, generator
