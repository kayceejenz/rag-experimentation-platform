begin;

create table ragapp.workspaces (
 id uuid primary key default gen_random_uuid(),
 name text not null,
 created_by uuid not null references ragapp.users(id) on delete restrict,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 deleted_at timestamptz,
 check(length(trim(name)) between 1 and 160)
);

create trigger workspaces_set_updated_at before update on ragapp.workspaces
for each row execute function ragapp.set_updated_at();

create table ragapp.workspace_members (
 workspace_id uuid not null references ragapp.workspaces(id) on delete cascade,
 user_id uuid not null references ragapp.users(id) on delete cascade,
 role ragapp.project_role not null,
 joined_at timestamptz not null default now(),
 primary key(workspace_id,user_id)
);

insert into ragapp.workspaces(id,name,created_by,created_at,updated_at)
select gen_random_uuid(),coalesce(nullif(trim(u.display_name),''),split_part(u.email,'@',1)) || '''s workspace',u.id,u.created_at,u.updated_at
from ragapp.users u where u.deleted_at is null;

insert into ragapp.workspace_members(workspace_id,user_id,role)
select w.id,w.created_by,'owner' from ragapp.workspaces w;

create function ragapp.create_personal_workspace()
returns trigger language plpgsql as $$
declare workspace uuid;
begin
 insert into ragapp.workspaces(name,created_by)
 values(coalesce(nullif(trim(new.display_name),''),split_part(new.email,'@',1)) || '''s workspace',new.id)
 returning id into workspace;
 insert into ragapp.workspace_members(workspace_id,user_id,role)
 values(workspace,new.id,'owner');
 return new;
end;
$$;

create trigger users_create_personal_workspace after insert on ragapp.users
for each row execute function ragapp.create_personal_workspace();

alter table ragapp.projects add column workspace_id uuid;
update ragapp.projects p set workspace_id=w.id from ragapp.workspaces w where w.created_by=p.owner_id;
alter table ragapp.projects alter column workspace_id set not null;
alter table ragapp.projects add constraint projects_workspace_fk
foreign key(workspace_id) references ragapp.workspaces(id) on delete cascade;
create index projects_workspace_active_idx on ragapp.projects(workspace_id,updated_at desc)
where deleted_at is null;

alter table ragapp.knowledge_bots rename to assistants;
alter table ragapp.assistants rename constraint knowledge_bots_pkey to assistants_pkey;
alter table ragapp.chats rename to conversations;
alter table ragapp.conversations rename column bot_id to assistant_id;

alter table ragapp.knowledge_bases drop column if exists chat_id;
alter table ragapp.knowledge_bases drop constraint knowledge_bases_bot_unique;
alter table ragapp.knowledge_bases drop constraint knowledge_bases_bot_project_fk;
alter table ragapp.knowledge_bases drop column bot_id;
alter table ragapp.knowledge_bases add column created_by uuid references ragapp.users(id) on delete set null;
update ragapp.knowledge_bases kb set created_by=p.owner_id from ragapp.projects p where p.id=kb.project_id;

alter table ragapp.messages rename column chat_id to conversation_id;

create table ragapp.assistant_revisions (
 id uuid primary key default gen_random_uuid(),
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 assistant_id uuid not null,
 version integer not null,
 index_specification_id uuid,
 retrieval_specification_id uuid,
 generation_specification_id uuid,
 created_by uuid references ragapp.users(id) on delete set null,
 created_at timestamptz not null default now(),
 unique(id,project_id),
 unique(assistant_id,version),
 foreign key(assistant_id,project_id) references ragapp.assistants(id,project_id) on delete cascade,
 foreign key(index_specification_id,project_id) references ragapp.specifications(id,project_id) on delete restrict,
 foreign key(retrieval_specification_id,project_id) references ragapp.specifications(id,project_id) on delete restrict,
 foreign key(generation_specification_id,project_id) references ragapp.specifications(id,project_id) on delete restrict,
 check(version > 0)
);

create trigger assistant_revisions_reject_update before update on ragapp.assistant_revisions
for each row execute function ragapp.reject_immutable_update();

alter table ragapp.assistants add column active_revision_id uuid;
alter table ragapp.assistants add constraint assistants_active_revision_fk
foreign key(active_revision_id,project_id) references ragapp.assistant_revisions(id,project_id) on delete restrict;

create table ragapp.benchmark_datasets (
 id uuid primary key default gen_random_uuid(),
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 name text not null,
 description text,
 version integer not null default 1,
 content jsonb not null default '[]'::jsonb,
 created_by uuid references ragapp.users(id) on delete set null,
 created_at timestamptz not null default now(),
 unique(project_id,name,version),
 check(length(trim(name)) between 1 and 160),
 check(version > 0),
 check(jsonb_typeof(content)='array')
);

create trigger benchmark_datasets_reject_update before update on ragapp.benchmark_datasets
for each row execute function ragapp.reject_immutable_update();

alter table ragapp.executions add column assistant_id uuid;
alter table ragapp.executions add column assistant_revision_id uuid;
alter table ragapp.executions add constraint executions_assistant_project_fk
foreign key(assistant_id,project_id) references ragapp.assistants(id,project_id) on delete restrict;
alter table ragapp.executions add constraint executions_assistant_revision_project_fk
foreign key(assistant_revision_id,project_id) references ragapp.assistant_revisions(id,project_id) on delete restrict;
alter table ragapp.executions add constraint executions_assistant_revision_pair_check
check((assistant_id is null and assistant_revision_id is null) or (assistant_id is not null and assistant_revision_id is not null));

create index executions_assistant_time_idx on ragapp.executions(assistant_id,created_at desc)
where assistant_id is not null;

commit;
