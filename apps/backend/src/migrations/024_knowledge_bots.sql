begin;

create table ragapp.knowledge_bots (
 id uuid primary key default gen_random_uuid(),
 project_id uuid not null references ragapp.projects(id) on delete cascade,
 created_by uuid not null references ragapp.users(id) on delete restrict,
 name text not null,
 description text,
 status text not null default 'active',
 settings jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 deleted_at timestamptz,
 unique(id,project_id),
 check(length(trim(name)) between 1 and 160),
 check(description is null or length(description) <= 2000),
 check(status in ('active','archived')),
 check(jsonb_typeof(settings)='object')
);

create index knowledge_bots_project_active_idx
 on ragapp.knowledge_bots(project_id,updated_at desc)
 where deleted_at is null;

create trigger knowledge_bots_set_updated_at
 before update on ragapp.knowledge_bots
 for each row execute function ragapp.set_updated_at();

insert into ragapp.knowledge_bots(
 id,project_id,created_by,name,status,settings,created_at,updated_at,deleted_at
)
select id,project_id,created_by,title,status::text,settings,created_at,updated_at,deleted_at
from ragapp.chats;

alter table ragapp.chats add column bot_id uuid;

update ragapp.chats set bot_id=id;

alter table ragapp.chats alter column bot_id set not null;
alter table ragapp.chats
 add constraint chats_bot_project_fk
 foreign key(bot_id,project_id)
 references ragapp.knowledge_bots(id,project_id) on delete cascade;

create index chats_bot_time_idx
 on ragapp.chats(bot_id,created_at,id)
 where deleted_at is null;

alter table ragapp.knowledge_bases add column bot_id uuid;

update ragapp.knowledge_bases kb
set bot_id=c.bot_id
from ragapp.chats c
where c.id=kb.chat_id;

alter table ragapp.knowledge_bases alter column bot_id set not null;
alter table ragapp.knowledge_bases
 add constraint knowledge_bases_bot_project_fk
 foreign key(bot_id,project_id)
 references ragapp.knowledge_bots(id,project_id) on delete cascade;
alter table ragapp.knowledge_bases
 add constraint knowledge_bases_bot_unique unique(bot_id);

alter table ragapp.knowledge_bases alter column chat_id drop not null;

commit;
