begin;

drop trigger if exists embedding_models_create_hnsw_index on ragapp.embedding_models;
drop function if exists ragapp.embedding_models_create_hnsw_index();

alter table ragapp.chunk_embeddings
  add column specification_id uuid references ragapp.specifications(id) on delete restrict;

update ragapp.chunk_embeddings embedding
set specification_id = chunk.specification_id
from ragapp.chunks chunk
where chunk.id = embedding.chunk_id
  and embedding.specification_id is null;

create index chunk_embeddings_specification_idx
  on ragapp.chunk_embeddings(specification_id, chunk_id);

create function ragapp.ensure_specification_hnsw_index(
  target_specification_id uuid,
  target_model_id uuid
)
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
  perform pg_advisory_xact_lock(hashtext(target_specification_id::text));

  if not exists (
    select 1 from ragapp.specifications
    where id = target_specification_id and kind = 'pipeline'
  ) then
    raise exception 'index specification % does not exist', target_specification_id;
  end if;

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

  index_name := 'chunk_embeddings_hnsw_' || replace(target_specification_id::text, '-', '');
  execute format(
    'create index if not exists %I on ragapp.chunk_embeddings using hnsw '
    '((embedding::%s(%s)) %s) where specification_id = %L::uuid',
    index_name,
    indexed_type,
    model_dimensions,
    operator_class,
    target_specification_id
  );
  return index_name;
end;
$$;

create temporary table specification_hnsw_targets on commit drop as
select distinct embedding.specification_id, embedding.embedding_model_id
from ragapp.chunk_embeddings embedding
where embedding.specification_id is not null;

do $$
declare
  existing record;
begin
  for existing in
    select specification_id, embedding_model_id
    from specification_hnsw_targets
  loop
    perform ragapp.ensure_specification_hnsw_index(
      existing.specification_id,
      existing.embedding_model_id
    );
  end loop;
end;
$$;

do $$
declare
  obsolete record;
begin
  for obsolete in
    select indexname
    from pg_indexes
    where schemaname = 'ragapp'
      and indexname like 'chunk_embeddings_hnsw_%'
      and indexdef like '%embedding_model_id%'
  loop
    execute format('drop index if exists ragapp.%I', obsolete.indexname);
  end loop;
end;
$$;

drop function if exists ragapp.ensure_embedding_hnsw_index(uuid);

commit;
