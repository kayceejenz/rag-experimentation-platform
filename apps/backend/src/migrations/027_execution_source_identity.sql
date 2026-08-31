begin;

create function ragapp.reject_execution_source_change()
returns trigger language plpgsql as $$
begin
 if old.knowledge_base_id is distinct from new.knowledge_base_id then
  raise exception 'execution source identity is immutable';
 end if;
 return new;
end;
$$;

create trigger executions_reject_source_change
before update on ragapp.executions
for each row execute function ragapp.reject_execution_source_change();

commit;
