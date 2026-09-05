begin;

alter table ragapp.ingestion_jobs add column specification_id uuid
references ragapp.specifications(id) on delete restrict;
create index ingestion_jobs_specification_idx on ragapp.ingestion_jobs(specification_id,created_at);

commit;
