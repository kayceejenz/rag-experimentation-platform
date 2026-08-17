begin;

create table ragapp.outbox_events (
 id uuid primary key default gen_random_uuid(), 
 topic text not null, 
 aggregate_type text not null,
 aggregate_id uuid not null, 
 payload jsonb not null, 
 created_at timestamptz not null default now(),
 published_at timestamptz, 
 attempts integer not null default 0, 
 last_error text, 
 check(jsonb_typeof(payload)='object')
);

create index outbox_events_unpublished_idx on ragapp.outbox_events(created_at) where published_at is null;
commit;
