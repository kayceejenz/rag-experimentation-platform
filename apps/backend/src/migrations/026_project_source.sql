begin;

insert into ragapp.knowledge_bases(project_id,created_by,name)
select p.id,p.owner_id,'Source' from ragapp.projects p
where p.deleted_at is null and not exists(
 select 1 from ragapp.knowledge_bases kb where kb.project_id=p.id and kb.deleted_at is null
);

create table ragapp.project_sources (
 project_id uuid primary key references ragapp.projects(id) on delete cascade,
 knowledge_base_id uuid not null unique,
 created_at timestamptz not null default now(),
 foreign key(knowledge_base_id,project_id)
 references ragapp.knowledge_bases(id,project_id) on delete restrict
);

insert into ragapp.project_sources(project_id,knowledge_base_id)
select distinct on(kb.project_id) kb.project_id,kb.id
from ragapp.knowledge_bases kb
join ragapp.projects p on p.id=kb.project_id
where kb.deleted_at is null and p.deleted_at is null
order by kb.project_id,kb.created_at,kb.id;

alter table ragapp.executions add column knowledge_base_id uuid;
alter table ragapp.executions add constraint executions_source_project_fk
foreign key(knowledge_base_id,project_id)
references ragapp.knowledge_bases(id,project_id) on delete restrict;
create index executions_source_time_idx on ragapp.executions(knowledge_base_id,created_at desc)
where knowledge_base_id is not null;

commit;
