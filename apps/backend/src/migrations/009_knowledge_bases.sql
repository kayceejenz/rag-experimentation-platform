begin;

create table ragapp.knowledge_bases (
 id uuid primary key default gen_random_uuid(), 
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 chat_id uuid not null unique, 
 name text not null default 'Chat knowledge base', 
 settings jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(), 
 updated_at timestamptz not null default now(),
 deleted_at timestamptz,
 foreign key(chat_id,project_id) references ragapp.chats(id,project_id) on delete cascade,
 check(length(trim(name)) between 1 and 160), 
 check(jsonb_typeof(settings)='object'), unique(id,project_id)
);

create index knowledge_bases_project_idx on ragapp.knowledge_bases(project_id,created_at desc) where deleted_at is null;
create trigger knowledge_bases_set_updated_at before update on ragapp.knowledge_bases for each row execute function ragapp.set_updated_at();
commit;
