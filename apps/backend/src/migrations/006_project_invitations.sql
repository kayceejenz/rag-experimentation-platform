begin;

create table ragapp.project_invitations (
 id uuid primary key default gen_random_uuid(), 
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 email text not null, 
 role ragapp.project_role not null default 'viewer', 
 token_hash text not null unique,
 invited_by uuid not null references ragapp.users(id) on delete restrict, 
 expires_at timestamptz not null,
 accepted_at timestamptz, created_at timestamptz not null default now(),
 check(email=lower(trim(email))), 
 check(role <> 'owner')
);

create index project_invitations_pending_idx on ragapp.project_invitations(project_id,expires_at) where accepted_at is null;
commit;
