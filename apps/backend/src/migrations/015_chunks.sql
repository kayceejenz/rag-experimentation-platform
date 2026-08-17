begin;

create table ragapp.chunks (
 id uuid primary key default gen_random_uuid(), 
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 knowledge_base_id uuid not null, 
 source_id uuid not null, 
 source_version_id uuid not null,
 position integer not null, 
 content text not null, 
 token_count integer, 
 page_from integer, 
 page_to integer,
 metadata jsonb not null default '{}'::jsonb, 
 search_vector tsvector generated always as(to_tsvector('english',content)) stored,
 created_at timestamptz not null default now(),
 foreign key(knowledge_base_id,project_id) references ragapp.knowledge_bases(id,project_id) on delete cascade,
 foreign key(source_id,project_id) references ragapp.sources(id,project_id) on delete cascade,
 foreign key(source_version_id,source_id) references ragapp.source_versions(id,source_id) on delete cascade,
 unique(source_version_id,position), 
 check(position>=0), check(length(trim(content))>0),
 check(token_count is null or token_count>=0), 
 check((page_from is null and page_to is null) or (page_from>0 and page_to>=page_from)),
 check(jsonb_typeof(metadata)='object')
);

create index chunks_knowledge_base_idx on ragapp.chunks(knowledge_base_id,source_version_id,position);
create index chunks_project_idx on ragapp.chunks(project_id,knowledge_base_id);
create index chunks_full_text_idx on ragapp.chunks using gin(search_vector);
commit;
