begin;

alter table ragapp.assistant_revisions
  add column experiment_variant_run_id uuid references ragapp.experiment_variant_runs(id) on delete restrict,
  add column configuration jsonb not null default '{}'::jsonb;

alter table ragapp.assistant_revisions
  add constraint assistant_revisions_configuration_object
  check(jsonb_typeof(configuration) = 'object');

create index assistant_revisions_variant_run_idx
  on ragapp.assistant_revisions(experiment_variant_run_id)
  where experiment_variant_run_id is not null;

commit;
