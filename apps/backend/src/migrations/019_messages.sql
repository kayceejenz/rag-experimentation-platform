begin;

create table ragapp.messages (
 id uuid primary key default gen_random_uuid(), 
 chat_id uuid not null references ragapp.chats(id) on delete cascade,
 parent_message_id uuid, 
 role ragapp.message_role not null, 
 status ragapp.message_status not null default 'completed',
 content text not null, 
 model_provider text, 
 model_name text, 
 prompt_tokens integer, 
 completion_tokens integer,
 latency_ms integer, 
 error_code text, 
 error_message text, 
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(), 
 completed_at timestamptz, 
 unique(id,chat_id),
 foreign key(parent_message_id,chat_id) references ragapp.messages(id,chat_id) on delete set null,
 check(length(content)>0 or status='failed'), 
 check((prompt_tokens is null or prompt_tokens>=0) and (completion_tokens is null or completion_tokens>=0) and (latency_ms is null or latency_ms>=0)),
 check(jsonb_typeof(metadata)='object')
);

create index messages_chat_time_idx on ragapp.messages(chat_id,created_at,id);
commit;
