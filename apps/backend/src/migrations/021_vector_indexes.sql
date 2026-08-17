begin;
-- ANN indexes require a fixed dimension. Create one per active model after registration:
-- create index concurrently chunk_embeddings_nomic_hnsw_idx
-- on ragapp.chunk_embeddings using hnsw ((embedding::vector(768)) vector_cosine_ops)
-- where embedding_model_id = '<model-uuid>';
commit;
