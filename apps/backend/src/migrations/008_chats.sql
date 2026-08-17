begin;

create table ragapp.chats (
 id uuid primary key default gen_random_uuid(), 
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 created_by uuid not null references ragapp.users(id) on delete restrict, 
 title text not null default 'New chat',
 status ragapp.chat_status not null default 'active',
 settings jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(), 
 updated_at timestamptz not null default now(), 
 deleted_at timestamptz,
 check(length(trim(title)) between 1 and 240), 
 check(jsonb_typeof(settings)='object'), 
 unique(id,project_id)
);

create index chats_project_active_idx on ragapp.chats(project_id,updated_at desc) where deleted_at is null;
create trigger chats_set_updated_at before update on ragapp.chats for each row execute function ragapp.set_updated_at();
commit;
