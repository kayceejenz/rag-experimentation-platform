begin;
create table ragapp.sources (
 id uuid primary key default gen_random_uuid(),
 project_id uuid not null, 
 knowledge_base_id uuid not null,
 uploaded_by uuid not null references ragapp.users(id) on delete restrict, 
 display_name text not null,
 created_at timestamptz not null default now(), 
 updated_at timestamptz not null default now(), 
 deleted_at timestamptz,
 foreign key(knowledge_base_id,project_id) references ragapp.knowledge_bases(id,project_id) on delete cascade,
 unique(id,project_id), 
 check(length(trim(display_name)) between 1 and 512)
);

create index sources_knowledge_base_active_idx on ragapp.sources(knowledge_base_id,created_at desc) where deleted_at is null;
create trigger sources_set_updated_at before update on ragapp.sources for each row execute function ragapp.set_updated_at();
commit;
