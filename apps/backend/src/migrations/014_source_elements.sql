begin;

create table ragapp.source_elements (
 id uuid primary key default gen_random_uuid(), 
 source_version_id uuid not null references ragapp.source_versions(id) on delete cascade,
 element_id text not null, 
 parent_element_id text, 
 category text not null, 
 content text not null default '',
 page_number integer, 
 coordinates jsonb, 
 table_html text, 
 visual_storage_key text,
 metadata jsonb not null default '{}'::jsonb, 
 sequence_number integer not null, 
 created_at timestamptz not null default now(),
 unique(source_version_id,element_id), 
 unique(source_version_id,sequence_number),
 check(page_number is null or page_number>0), 
 check(sequence_number>=0), 
 check(jsonb_typeof(metadata)='object')
);

create index source_elements_version_page_idx on ragapp.source_elements(source_version_id,page_number,sequence_number);
commit;
