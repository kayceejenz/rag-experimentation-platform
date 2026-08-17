begin;

create table ragapp.ingestion_jobs (
 id uuid primary key default gen_random_uuid(), 
 source_version_id uuid not null references ragapp.source_versions(id) on delete cascade,
 status ragapp.job_status not null default 'queued', 
 priority smallint not null default 100,
 attempts integer not null default 0, 
 max_attempts integer not null default 5, 
 available_at timestamptz not null default now(),
 locked_at timestamptz, 
 locked_by text, 
 lease_expires_at timestamptz, 
 last_error text,
 created_at timestamptz not null default now(), 
 updated_at timestamptz not null default now(), 
 completed_at timestamptz,
 check(attempts>=0 and max_attempts>0 and attempts<=max_attempts)
);

create unique index ingestion_jobs_one_active_per_version_idx on ragapp.ingestion_jobs(source_version_id) where status in ('queued','running');
create index ingestion_jobs_claim_idx on ragapp.ingestion_jobs(priority,available_at,created_at) where status='queued';
create index ingestion_jobs_lease_idx on ragapp.ingestion_jobs(lease_expires_at) where status='running';
create trigger ingestion_jobs_set_updated_at before update on ragapp.ingestion_jobs for each row execute function ragapp.set_updated_at();
commit;
