begin;

alter table ragapp.ingestion_jobs add column stage text not null default 'chunk';
alter table ragapp.ingestion_jobs add constraint ingestion_jobs_stage_check
check(stage in ('chunk','index'));
drop index ragapp.ingestion_jobs_one_active_per_version_idx;
create unique index ingestion_jobs_one_active_stage_per_version_idx
on ragapp.ingestion_jobs(source_version_id,stage) where status in ('queued','running');

alter table ragapp.source_versions alter column status set default 'uploaded';

commit;
