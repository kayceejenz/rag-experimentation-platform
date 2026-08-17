begin;

create table ragapp.chunk_embeddings (
 chunk_id uuid not null references ragapp.chunks(id) on delete cascade,
 embedding_model_id uuid not null references ragapp.embedding_models(id) on delete restrict,
 embedding vector not null, created_at timestamptz not null default now(), primary key(chunk_id,embedding_model_id)
);

create function ragapp.validate_embedding_dimensions() returns trigger language plpgsql as $$

declare expected integer; 
begin select dimensions into expected from ragapp.embedding_models where id=new.embedding_model_id;
if vector_dims(new.embedding)<>expected then raise exception 'embedding dimension mismatch'; 
end if; 
return new;
end; 
$$;

create trigger chunk_embeddings_validate_dimensions before insert or update on ragapp.chunk_embeddings for each row execute function ragapp.validate_embedding_dimensions();
create index chunk_embeddings_model_idx on ragapp.chunk_embeddings(embedding_model_id);
commit;
