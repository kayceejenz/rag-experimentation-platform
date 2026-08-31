begin;

drop index if exists ragapp.ingestion_jobs_one_active_stage_per_version_idx;

create unique index ingestion_jobs_one_active_stage_per_specification_idx
on ragapp.ingestion_jobs(
  source_version_id,
  stage,
  coalesce(specification_id, '00000000-0000-0000-0000-000000000000'::uuid)
)
where status in ('queued','running');

commit;
