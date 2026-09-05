begin;
create table ragapp.experiment_runs(
 id uuid primary key default gen_random_uuid(), project_id uuid not null, experiment_id uuid not null,
 status ragapp.execution_status not null default 'pending', code_revision text not null,
 created_by uuid references ragapp.users(id) on delete set null, created_at timestamptz not null default now(),
 started_at timestamptz, completed_at timestamptz, worker_id text, error_message text,
 foreign key(experiment_id,project_id) references ragapp.experiments(id,project_id) on delete restrict
);
create index experiment_runs_claim_idx on ragapp.experiment_runs(created_at) where status='pending';
create index experiment_runs_experiment_idx on ragapp.experiment_runs(experiment_id,created_at desc);
create table ragapp.experiment_variant_runs(
 id uuid primary key default gen_random_uuid(),run_id uuid not null references ragapp.experiment_runs(id) on delete cascade,
 variant_id uuid not null,project_id uuid not null,status ragapp.execution_status not null default 'pending',
 aggregate_metrics jsonb,error_message text,started_at timestamptz,completed_at timestamptz,
 unique(run_id,variant_id),foreign key(variant_id,project_id) references ragapp.experiment_variants(id,project_id) on delete restrict,
 check(aggregate_metrics is null or jsonb_typeof(aggregate_metrics)='object')
);
create table ragapp.experiment_case_results(
 id uuid primary key default gen_random_uuid(),variant_run_id uuid not null references ragapp.experiment_variant_runs(id) on delete cascade,
 case_id uuid not null,position integer not null,question text not null,reference_answer text,
 retrieved_context jsonb not null,generated_answer text,metrics jsonb not null,error_message text,
 created_at timestamptz not null default now(),unique(variant_run_id,case_id),
 check(position>=0),check(jsonb_typeof(retrieved_context)='array'),check(jsonb_typeof(metrics)='object')
);
create trigger experiment_case_results_reject_update before update on ragapp.experiment_case_results for each row execute function ragapp.reject_immutable_update();
commit;
