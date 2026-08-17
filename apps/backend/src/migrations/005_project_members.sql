begin;

create table ragapp.project_members (
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 user_id uuid not null references ragapp.users(id) on delete cascade,
 role ragapp.project_role not null, 
 joined_at timestamptz not null default now(), 
 primary key(project_id,user_id)
);

create index project_members_user_idx on ragapp.project_members(user_id, project_id);

create function ragapp.add_project_owner_membership() returns trigger language plpgsql as $$

begin insert into ragapp.project_members(project_id,user_id,role) values(new.id,new.owner_id,'owner'); return new; end; $$;

create trigger projects_add_owner_membership after insert on ragapp.projects for each row execute function ragapp.add_project_owner_membership();

commit;
