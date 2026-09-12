begin;

create table ragapp.auth_rate_limits (
  action text not null,
  client_key text not null,
  window_started_at timestamptz not null,
  attempt_count integer not null,
  primary key (action, client_key),
  check (action in ('register', 'login')),
  check (attempt_count > 0)
);

create index auth_rate_limits_window_idx
  on ragapp.auth_rate_limits (window_started_at);

commit;
