begin;

alter table ragapp.project_member_permissions drop constraint project_member_permissions_feature_check;
alter table ragapp.project_member_permissions add constraint project_member_permissions_feature_check
check(feature in ('knowledge','indexes','experiments','benchmarks','prompts','assistants','runs','settings'));

insert into ragapp.project_member_permissions(project_id,user_id,feature,can_view,can_manage)
select project_id,user_id,'prompts',true,(role='editor') from ragapp.project_members
where role<>'owner' on conflict do nothing;

create table ragapp.prompts (
 id uuid primary key default gen_random_uuid(),
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 name text not null,
 purpose text,
 description text,
 prompt_type text not null,
 status text not null default 'active',
 created_by uuid references ragapp.users(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(id,project_id),
 check(length(trim(name)) between 1 and 160),
 check(prompt_type in ('system','rag_answer','evaluation')),
 check(status in ('active','archived'))
);
create unique index prompts_project_name_active_idx on ragapp.prompts(project_id,lower(name)) where status='active';
create trigger prompts_set_updated_at before update on ragapp.prompts for each row execute function ragapp.set_updated_at();

create table ragapp.prompt_versions (
 id uuid primary key default gen_random_uuid(),
 prompt_id uuid not null,
 project_id uuid not null,
 version integer not null,
 template text not null,
 variables jsonb not null,
 content_sha256 text not null,
 change_note text,
 created_by uuid references ragapp.users(id) on delete set null,
 created_at timestamptz not null default now(),
 unique(prompt_id,version),
 unique(prompt_id,content_sha256),
 foreign key(prompt_id,project_id) references ragapp.prompts(id,project_id) on delete cascade,
 check(version>0),
 check(length(trim(template))>0),
 check(jsonb_typeof(variables)='array'),
 check(content_sha256 ~ '^[0-9a-f]{64}$')
);
create index prompt_versions_prompt_version_idx on ragapp.prompt_versions(prompt_id,version desc);
create trigger prompt_versions_reject_update before update on ragapp.prompt_versions for each row execute function ragapp.reject_immutable_update();

commit;
