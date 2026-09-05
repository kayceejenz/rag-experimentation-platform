begin;

create function ragapp.ensure_embedding_hnsw_index(target_model_id uuid)
returns text
language plpgsql
as $$
declare
  model_dimensions integer;
  model_distance text;
  index_name text;
  indexed_type text;
  operator_class text;
begin
  perform pg_advisory_xact_lock(hashtext(target_model_id::text));

  select dimensions, distance_metric
  into model_dimensions, model_distance
  from ragapp.embedding_models
  where id = target_model_id;

  if not found then
    raise exception 'embedding model % does not exist', target_model_id;
  end if;
  if model_dimensions > 4000 then
    raise exception 'HNSW supports at most 4000 dimensions with halfvec';
  end if;

  indexed_type := case when model_dimensions <= 2000 then 'vector' else 'halfvec' end;
  operator_class := case model_distance
    when 'cosine' then indexed_type || '_cosine_ops'
    when 'l2' then indexed_type || '_l2_ops'
    when 'inner_product' then indexed_type || '_ip_ops'
    else null
  end;
  if operator_class is null then
    raise exception 'unsupported embedding distance metric %', model_distance;
  end if;

  index_name := 'chunk_embeddings_hnsw_' || replace(target_model_id::text, '-', '');
  execute format(
    'create index if not exists %I on ragapp.chunk_embeddings using hnsw '
    '((embedding::%s(%s)) %s) where embedding_model_id = %L::uuid',
    index_name,
    indexed_type,
    model_dimensions,
    operator_class,
    target_model_id
  );
  return index_name;
end;
$$;

create function ragapp.embedding_models_create_hnsw_index()
returns trigger
language plpgsql
as $$
begin
  perform ragapp.ensure_embedding_hnsw_index(new.id);
  return new;
end;
$$;

create trigger embedding_models_create_hnsw_index
after insert on ragapp.embedding_models
for each row execute function ragapp.embedding_models_create_hnsw_index();

select ragapp.ensure_embedding_hnsw_index(id)
from ragapp.embedding_models
where is_active and dimensions <= 4000;

commit;
