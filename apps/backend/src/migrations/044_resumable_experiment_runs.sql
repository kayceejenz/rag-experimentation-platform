begin;

alter table ragapp.experiment_runs
  add column heartbeat_at timestamptz,
  add column attempt integer not null default 0 check(attempt >= 0);

drop index ragapp.experiment_runs_claim_idx;
create index experiment_runs_claim_idx
  on ragapp.experiment_runs(status, heartbeat_at, created_at)
  where status in ('pending', 'running');

commit;
