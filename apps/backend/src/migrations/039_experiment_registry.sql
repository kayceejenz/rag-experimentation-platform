begin;

alter table ragapp.benchmark_datasets
  add constraint benchmark_datasets_id_project_unique unique(id, project_id);
alter table ragapp.prompt_versions
  add constraint prompt_versions_id_project_unique unique(id, project_id);

create table ragapp.experiments (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references ragapp.projects(id) on delete cascade,
  name text not null,
  description text,
  hypothesis text not null,
  benchmark_dataset_id uuid not null,
  metrics jsonb not null,
  primary_metric text not null,
  status text not null default 'draft',
  created_by uuid references ragapp.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(id, project_id),
  foreign key(benchmark_dataset_id, project_id)
    references ragapp.benchmark_datasets(id, project_id) on delete restrict,
  check(length(trim(name)) between 1 and 160),
  check(length(trim(hypothesis)) > 0),
  check(jsonb_typeof(metrics) = 'array' and jsonb_array_length(metrics) > 0),
  check(status in ('draft', 'ready', 'completed', 'archived'))
);

create unique index experiments_project_active_name_idx
  on ragapp.experiments(project_id, lower(name))
  where status <> 'archived';
create index experiments_project_updated_idx
  on ragapp.experiments(project_id, updated_at desc);
create trigger experiments_set_updated_at before update on ragapp.experiments
for each row execute function ragapp.set_updated_at();

create table ragapp.experiment_variants (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  experiment_id uuid not null,
  name text not null,
  index_specification_id uuid not null,
  system_prompt_version_id uuid not null,
  rag_prompt_version_id uuid not null,
  evaluator_prompt_versions jsonb not null,
  retrieval_configuration jsonb not null,
  generation_configuration jsonb not null,
  configuration_hash text not null,
  created_by uuid references ragapp.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(id, project_id),
  unique(experiment_id, name),
  unique(experiment_id, configuration_hash),
  foreign key(experiment_id, project_id)
    references ragapp.experiments(id, project_id) on delete cascade,
  foreign key(index_specification_id, project_id)
    references ragapp.specifications(id, project_id) on delete restrict,
  foreign key(system_prompt_version_id, project_id)
    references ragapp.prompt_versions(id, project_id) on delete restrict,
  foreign key(rag_prompt_version_id, project_id)
    references ragapp.prompt_versions(id, project_id) on delete restrict,
  check(length(trim(name)) between 1 and 160),
  check(jsonb_typeof(evaluator_prompt_versions) = 'object'),
  check(jsonb_typeof(retrieval_configuration) = 'object'),
  check(jsonb_typeof(generation_configuration) = 'object'),
  check(configuration_hash ~ '^[0-9a-f]{64}$')
);

create index experiment_variants_experiment_idx
  on ragapp.experiment_variants(experiment_id, created_at);
create trigger experiment_variants_reject_update before update on ragapp.experiment_variants
for each row execute function ragapp.reject_immutable_update();

commit;
