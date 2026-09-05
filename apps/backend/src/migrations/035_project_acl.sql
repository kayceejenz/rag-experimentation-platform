begin;

create table ragapp.project_member_permissions (
 project_id uuid not null,
 user_id uuid not null,
 feature text not null,
 can_view boolean not null default false,
 can_manage boolean not null default false,
 updated_at timestamptz not null default now(),
 primary key(project_id,user_id,feature),
 foreign key(project_id,user_id) references ragapp.project_members(project_id,user_id) on delete cascade,
 check(feature in ('knowledge','indexes','experiments','benchmarks','assistants','runs','settings')),
 check(not can_manage or can_view)
);

insert into ragapp.project_member_permissions(project_id,user_id,feature,can_view,can_manage)
select pm.project_id,pm.user_id,feature,true,(pm.role='editor')
from ragapp.project_members pm
cross join unnest(array['knowledge','indexes','experiments','benchmarks','assistants','runs','settings']) feature
where pm.role <> 'owner';

create function ragapp.has_project_permission(
 requested_project_id uuid,
 requested_user_id uuid,
 requested_feature text,
 requested_action text default 'view'
) returns boolean language sql stable as $$
 select exists(
  select 1 from ragapp.project_members pm
  where pm.project_id=requested_project_id and pm.user_id=requested_user_id
  and (
   pm.role='owner'
   or exists(
    select 1 from ragapp.project_member_permissions permission
    where permission.project_id=pm.project_id and permission.user_id=pm.user_id
    and permission.feature=requested_feature
    and case when requested_action='manage' then permission.can_manage else permission.can_view end
   )
  )
 );
$$;

commit;
