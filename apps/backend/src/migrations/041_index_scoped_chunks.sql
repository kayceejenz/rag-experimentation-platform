begin;

alter table ragapp.chunks
  add column specification_id uuid references ragapp.specifications(id) on delete restrict;

update ragapp.chunks chunk
set specification_id = (
  select job.specification_id
  from ragapp.ingestion_jobs job
  where job.source_version_id = chunk.source_version_id
    and job.stage = 'chunk'
    and job.specification_id is not null
  order by job.completed_at desc nulls last, job.created_at desc
  limit 1
)
where chunk.specification_id is null
  and exists (
    select 1 from ragapp.ingestion_jobs job
    where job.source_version_id = chunk.source_version_id
      and job.stage = 'chunk'
      and job.specification_id is not null
  );

alter table ragapp.chunks
  drop constraint chunks_source_version_id_position_key;

create unique index chunks_specification_version_position_idx
  on ragapp.chunks(specification_id, source_version_id, position)
  where specification_id is not null;

create unique index chunks_legacy_version_position_idx
  on ragapp.chunks(source_version_id, position)
  where specification_id is null;

create index chunks_specification_source_idx
  on ragapp.chunks(specification_id, source_version_id, position);

commit;
