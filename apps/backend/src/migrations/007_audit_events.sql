begin;

create table ragapp.audit_events (
 id bigint generated always as identity primary key, 
 project_id uuid references ragapp.projects(id) on delete set null,
 actor_user_id uuid references ragapp.users(id) on delete set null, 
 event_type text not null,
 entity_type text not null, 
 entity_id uuid, 
 payload jsonb not null default '{}'::jsonb,
 occurred_at timestamptz not null default now(), 
 check(jsonb_typeof(payload)='object')
);

create index audit_events_project_time_idx on ragapp.audit_events(project_id,occurred_at desc);
commit;
