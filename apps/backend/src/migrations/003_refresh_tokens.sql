begin;

create table ragapp.refresh_tokens (
 id uuid primary key default gen_random_uuid(), 
 user_id uuid not null references ragapp.users(id) on delete cascade,
 family_id uuid not null, 
 token_hash text not null unique,
 replaced_by_token_id uuid references ragapp.refresh_tokens(id) on delete set null,
 user_agent text, 
 ip_address inet, 
 created_at timestamptz not null default now(),
 expires_at timestamptz not null, 
 last_used_at timestamptz, 
 revoked_at timestamptz, 
 revoke_reason text,
 check (token_hash ~ '^[0-9a-f]{64}$'), 
 check (expires_at > created_at)
);

create index refresh_tokens_user_active_idx on ragapp.refresh_tokens(user_id, expires_at desc) where revoked_at is null;

create index refresh_tokens_family_idx on ragapp.refresh_tokens(family_id, created_at);

commit;
