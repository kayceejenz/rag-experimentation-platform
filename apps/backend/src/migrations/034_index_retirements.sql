begin;

create table ragapp.index_retirements (
  specification_id uuid primary key,
  project_id uuid not null,
  retired_by uuid references ragapp.users(id) on delete set null,
  retired_at timestamptz not null default now(),
  foreign key(specification_id, project_id)
    references ragapp.specifications(id, project_id) on delete cascade
);

create index index_retirements_project_time_idx
on ragapp.index_retirements(project_id, retired_at desc);

commit;
