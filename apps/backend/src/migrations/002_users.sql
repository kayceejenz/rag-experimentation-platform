begin;

create table ragapp.users (
 id uuid primary key default gen_random_uuid(),
 email text not null,
 password_hash text not null,
 display_name text, 
 avatar_url text, 
 is_active boolean not null default true,
 failed_login_attempts integer not null default 0,
 locked_until timestamptz,
 token_version integer not null default 0,
 password_changed_at timestamptz not null default now(),
 last_login_at timestamptz, 
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(), 
 deleted_at timestamptz,
 check (email = lower(trim(email))),
 check (length(trim(email)) between 3 and 320),
 check (length(password_hash) >= 20), 
 check (failed_login_attempts >= 0), 
 check (token_version >= 0)
);

create unique index users_email_unique_idx on ragapp.users(email) where deleted_at is null;

create trigger users_set_updated_at before update on ragapp.users for each row execute function ragapp.set_updated_at();

commit;
