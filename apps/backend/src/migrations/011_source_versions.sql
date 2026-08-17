begin;

create table ragapp.source_versions (
 id uuid primary key default gen_random_uuid(), 
 source_id uuid not null references ragapp.sources(id) on delete cascade,
 version integer not null, 
 filename text not null, 
 content_type text not null, 
 byte_size bigint not null,
 content_sha256 text not null, 
 storage_key text not null unique,
 status ragapp.source_status not null default 'uploaded',
 parser_name text, 
 parser_version text, 
 parser_config jsonb not null default '{}'::jsonb,
 element_count integer not null default 0, 
 chunk_count integer not null default 0,
 error_code text, 
 error_message text, 
 created_at timestamptz not null default now(),
 processing_started_at timestamptz, 
 processing_completed_at timestamptz,
 unique(source_id,version), 
 unique(id,source_id), 
 check(version>0), 
 check(byte_size>=0),
 check(content_sha256 ~ '^[0-9a-f]{64}$'), 
 check(jsonb_typeof(parser_config)='object')
);

create index source_versions_source_idx on ragapp.source_versions(source_id,version desc);
create index source_versions_hash_idx on ragapp.source_versions(content_sha256);
commit;
