begin;

alter table ragapp.users add column default_project_id uuid;

do $$
declare
 account record;
 workspace uuid;
 project uuid;
 source uuid;
begin
 for account in select id from ragapp.users where deleted_at is null loop
  select p.id into project
  from ragapp.projects p
  where p.owner_id=account.id and p.deleted_at is null
  order by p.created_at,p.id limit 1;

  if project is null then
   select wm.workspace_id into workspace
   from ragapp.workspace_members wm
   where wm.user_id=account.id and wm.role='owner'
   order by wm.joined_at,wm.workspace_id limit 1;

   insert into ragapp.projects(workspace_id,owner_id,name)
   values(workspace,account.id,'My Project') returning id into project;
  end if;

  if not exists(select 1 from ragapp.project_sources ps where ps.project_id=project) then
   select kb.id into source
   from ragapp.knowledge_bases kb
   where kb.project_id=project and kb.deleted_at is null
   order by kb.created_at,kb.id limit 1;

   if source is null then
    insert into ragapp.knowledge_bases(project_id,created_by,name)
    values(project,account.id,'Source') returning id into source;
   end if;

   insert into ragapp.project_sources(project_id,knowledge_base_id)
   values(project,source);
  end if;

  update ragapp.users set default_project_id=project where id=account.id;
 end loop;
end;
$$;

alter table ragapp.users add constraint users_default_project_fk
foreign key(default_project_id) references ragapp.projects(id) on delete restrict;

create index users_default_project_idx on ragapp.users(default_project_id);

create or replace function ragapp.create_personal_workspace()
returns trigger language plpgsql as $$
declare
 workspace uuid;
 project uuid;
 source uuid;
begin
 insert into ragapp.workspaces(name,created_by)
 values(coalesce(nullif(trim(new.display_name),''),split_part(new.email,'@',1)) || '''s workspace',new.id)
 returning id into workspace;

 insert into ragapp.workspace_members(workspace_id,user_id,role)
 values(workspace,new.id,'owner');

 insert into ragapp.projects(workspace_id,owner_id,name)
 values(workspace,new.id,'My Project') returning id into project;

 insert into ragapp.knowledge_bases(project_id,created_by,name)
 values(project,new.id,'Source') returning id into source;

 insert into ragapp.project_sources(project_id,knowledge_base_id)
 values(project,source);

 update ragapp.users set default_project_id=project where id=new.id;
 return new;
end;
$$;

commit;
