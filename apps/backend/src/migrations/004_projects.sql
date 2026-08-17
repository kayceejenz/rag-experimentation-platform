begin;

create table ragapp.projects (
 id uuid primary key default gen_random_uuid(), 
 owner_id uuid not null references ragapp.users(id) on delete restrict,
 name text not null, 
 description text, 
 settings jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(), 
 updated_at timestamptz not null default now(), 
 deleted_at timestamptz,
 check (length(trim(name)) between 1 and 160), 
 check (jsonb_typeof(settings) = 'object')
);

create index projects_owner_active_idx on ragapp.projects(owner_id, created_at desc) where deleted_at is null;

create trigger projects_set_updated_at before update on ragapp.projects for each row execute function ragapp.set_updated_at();

commit;
