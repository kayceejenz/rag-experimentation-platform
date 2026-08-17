begin;

create table ragapp.message_citations (
 id uuid primary key default gen_random_uuid(), 
 message_id uuid not null references ragapp.messages(id) on delete cascade,
 chunk_id uuid references ragapp.chunks(id) on delete set null, 
 source_id uuid references ragapp.sources(id) on delete set null,
 source_version_id uuid references ragapp.source_versions(id) on delete set null, 
 citation_order integer not null,
 source_filename text not null, 
 excerpt text not null, 
 page_from integer, 
 page_to integer,
 element_ids text[] not null default '{}', 
 coordinates jsonb not null default '[]'::jsonb,
 retrieval_score double precision, 
 created_at timestamptz not null default now(), 
 unique(message_id,citation_order),
 check(citation_order>=0), 
 check((page_from is null and page_to is null) or (page_from>0 and page_to>=page_from)),
 check(jsonb_typeof(coordinates)='array')
);

create index message_citations_message_idx on ragapp.message_citations(message_id,citation_order);
commit;
