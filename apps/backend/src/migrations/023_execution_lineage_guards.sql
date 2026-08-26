begin;

create function ragapp.validate_execution_artifact_link()
returns trigger
language plpgsql
as $$
declare
  execution_state ragapp.execution_status;
  required_state ragapp.execution_status;
begin
  select status into execution_state
  from ragapp.executions
  where id = new.execution_id and project_id = new.project_id;

  if execution_state is null then
    raise exception 'execution % does not exist in project %',
      new.execution_id, new.project_id;
  end if;

  if tg_table_name = 'execution_inputs' then
    required_state := 'pending';
  else
    required_state := 'running';
  end if;

  if execution_state <> required_state then
    raise exception '% can only be linked while execution is %',
      tg_table_name, required_state;
  end if;

  return new;
end;
$$;

create trigger execution_inputs_validate_state
before insert on ragapp.execution_inputs
for each row execute function ragapp.validate_execution_artifact_link();

create trigger execution_outputs_validate_state
before insert on ragapp.execution_outputs
for each row execute function ragapp.validate_execution_artifact_link();

commit;
