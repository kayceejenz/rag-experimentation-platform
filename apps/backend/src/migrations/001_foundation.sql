begin;

create extension if not exists pgcrypto;
create extension if not exists vector;

create schema if not exists ragapp;

create type ragapp.project_role as enum ('owner', 'editor', 'viewer');
create type ragapp.chat_status as enum ('active', 'archived');
create type ragapp.source_status as enum (
  'uploaded', 'queued', 'processing', 'ready', 'failed', 'archived'
);
create type ragapp.job_status as enum ('queued', 'running', 'completed', 'failed', 'cancelled');
create type ragapp.message_role as enum ('user', 'assistant', 'system', 'tool');
create type ragapp.message_status as enum ('pending', 'completed', 'failed');

create function ragapp.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

commit;
