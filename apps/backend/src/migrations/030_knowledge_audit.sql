begin;

alter table ragapp.audit_events add column knowledge_base_id uuid;
create index audit_events_knowledge_time_idx
on ragapp.audit_events(knowledge_base_id,occurred_at desc,id desc);

insert into ragapp.audit_events(
 project_id,knowledge_base_id,actor_user_id,event_type,entity_type,entity_id,payload,occurred_at
)
select s.project_id,s.knowledge_base_id,s.uploaded_by,'knowledge.document_uploaded','source',s.id,
 jsonb_build_object(
  'filename',sv.filename,
  'version',sv.version,
  'byte_size',sv.byte_size,
  'content_type',sv.content_type
 ),sv.created_at
from ragapp.sources s
join ragapp.source_versions sv on sv.source_id=s.id;

create trigger audit_events_reject_change before update or delete on ragapp.audit_events
for each row execute function ragapp.reject_immutable_update();

commit;
