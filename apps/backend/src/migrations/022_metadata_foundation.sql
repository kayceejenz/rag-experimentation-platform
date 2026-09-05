begin;

create type ragapp.execution_status as enum (
  'pending',
  'running',
  'completed',
  'failed',
  'cancelled'
);

create function ragapp.reject_immutable_update()
returns trigger
language plpgsql
as $$
begin
  raise exception '% records are immutable', tg_table_name;
end;
$$;

create table ragapp.specifications (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references ragapp.projects(id) on delete cascade,
  kind text not null,
  schema_version integer not null,
  configuration jsonb not null,
  configuration_hash text not null,
  created_by uuid references ragapp.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(id, project_id),
  unique(project_id, kind, schema_version, configuration_hash),
  check(kind ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(schema_version > 0),
  check(jsonb_typeof(configuration) = 'object'),
  check(configuration_hash ~ '^[0-9a-f]{64}$')
);

create index specifications_project_kind_idx
  on ragapp.specifications(project_id, kind, created_at desc);

create trigger specifications_reject_update
before update on ragapp.specifications
for each row execute function ragapp.reject_immutable_update();

create table ragapp.specification_dependencies (
  project_id uuid not null,
  specification_id uuid not null,
  dependency_id uuid not null,
  role text not null,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  primary key(specification_id, role, position),
  unique(specification_id, dependency_id, role),
  foreign key(specification_id, project_id)
    references ragapp.specifications(id, project_id) on delete cascade,
  foreign key(dependency_id, project_id)
    references ragapp.specifications(id, project_id) on delete restrict,
  check(specification_id <> dependency_id),
  check(role ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(position >= 0)
);

create index specification_dependencies_dependency_idx
  on ragapp.specification_dependencies(dependency_id, specification_id);

create table ragapp.artifacts (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references ragapp.projects(id) on delete cascade,
  kind text not null,
  storage_type text not null,
  storage_key text,
  content_sha256 text,
  manifest jsonb,
  manifest_hash text,
  media_type text,
  byte_size bigint,
  created_by uuid references ragapp.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(id, project_id),
  check(kind ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(storage_type in ('object', 'database', 'external')),
  check(storage_key is null or length(trim(storage_key)) > 0),
  check(content_sha256 is null or content_sha256 ~ '^[0-9a-f]{64}$'),
  check(manifest is null or jsonb_typeof(manifest) = 'object'),
  check(manifest_hash is null or manifest_hash ~ '^[0-9a-f]{64}$'),
  check(content_sha256 is not null or manifest_hash is not null),
  check(byte_size is null or byte_size >= 0)
);

create unique index artifacts_content_identity_idx
  on ragapp.artifacts(project_id, kind, content_sha256)
  where content_sha256 is not null;

create unique index artifacts_manifest_identity_idx
  on ragapp.artifacts(project_id, kind, manifest_hash)
  where manifest_hash is not null;

create unique index artifacts_storage_location_idx
  on ragapp.artifacts(project_id, storage_type, storage_key)
  where storage_key is not null;

create index artifacts_project_kind_idx
  on ragapp.artifacts(project_id, kind, created_at desc);

create trigger artifacts_reject_update
before update on ragapp.artifacts
for each row execute function ragapp.reject_immutable_update();

create table ragapp.executions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references ragapp.projects(id) on delete cascade,
  kind text not null,
  specification_id uuid,
  status ragapp.execution_status not null default 'pending',
  idempotency_key text,
  code_revision text not null,
  worker_id text,
  attempt integer not null default 1,
  parameters jsonb not null default '{}'::jsonb,
  result_summary jsonb,
  error_code text,
  error_message text,
  created_by uuid references ragapp.users(id) on delete set null,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  unique(id, project_id),
  foreign key(specification_id, project_id)
    references ragapp.specifications(id, project_id) on delete restrict,
  check(kind ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(idempotency_key is null or length(trim(idempotency_key)) > 0),
  check(length(trim(code_revision)) > 0),
  check(worker_id is null or length(trim(worker_id)) > 0),
  check(attempt > 0),
  check(jsonb_typeof(parameters) = 'object'),
  check(result_summary is null or jsonb_typeof(result_summary) = 'object'),
  check(
    (status = 'pending' and started_at is null and completed_at is null
      and result_summary is null and error_code is null and error_message is null)
    or (status = 'running' and started_at is not null and completed_at is null
      and result_summary is null and error_code is null and error_message is null)
    or (status = 'completed' and started_at is not null and completed_at is not null
      and error_code is null and error_message is null)
    or (status = 'failed' and started_at is not null and completed_at is not null
      and (error_code is not null or error_message is not null))
    or (status = 'cancelled' and completed_at is not null)
  ),
  check(started_at is null or started_at >= created_at),
  check(completed_at is null or completed_at >= coalesce(started_at, created_at))
);

create unique index executions_idempotency_idx
  on ragapp.executions(project_id, kind, idempotency_key)
  where idempotency_key is not null;

create index executions_project_kind_time_idx
  on ragapp.executions(project_id, kind, created_at desc);

create index executions_status_created_idx
  on ragapp.executions(status, created_at)
  where status in ('pending', 'running');

create function ragapp.validate_execution_transition()
returns trigger
language plpgsql
as $$
begin
  if old.project_id <> new.project_id
     or old.kind <> new.kind
     or old.specification_id is distinct from new.specification_id
     or old.idempotency_key is distinct from new.idempotency_key
     or old.code_revision <> new.code_revision
     or old.attempt <> new.attempt
     or old.parameters <> new.parameters
     or old.created_by is distinct from new.created_by
     or old.created_at <> new.created_at then
    raise exception 'execution identity and inputs are immutable';
  end if;

  if old.status in ('completed', 'failed', 'cancelled') then
    raise exception 'terminal execution % cannot be updated', old.id;
  end if;

  if not (
    (old.status = 'pending' and new.status in ('running', 'cancelled'))
    or (old.status = 'running' and new.status in ('completed', 'failed', 'cancelled'))
  ) then
    raise exception 'invalid execution transition from % to %', old.status, new.status;
  end if;

  return new;
end;
$$;

create trigger executions_validate_transition
before update on ragapp.executions
for each row execute function ragapp.validate_execution_transition();

create table ragapp.execution_inputs (
  project_id uuid not null,
  execution_id uuid not null,
  artifact_id uuid not null,
  role text not null,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  primary key(execution_id, role, position),
  unique(execution_id, artifact_id, role),
  foreign key(execution_id, project_id)
    references ragapp.executions(id, project_id) on delete cascade,
  foreign key(artifact_id, project_id)
    references ragapp.artifacts(id, project_id) on delete restrict,
  check(role ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(position >= 0)
);

create index execution_inputs_artifact_idx
  on ragapp.execution_inputs(artifact_id, execution_id);

create table ragapp.execution_outputs (
  project_id uuid not null,
  execution_id uuid not null,
  artifact_id uuid not null,
  role text not null,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  primary key(execution_id, role, position),
  unique(artifact_id),
  foreign key(execution_id, project_id)
    references ragapp.executions(id, project_id) on delete cascade,
  foreign key(artifact_id, project_id)
    references ragapp.artifacts(id, project_id) on delete restrict,
  check(role ~ '^[a-z][a-z0-9_]{1,63}$'),
  check(position >= 0)
);

create index execution_outputs_execution_idx
  on ragapp.execution_outputs(execution_id, role, position);

commit;
