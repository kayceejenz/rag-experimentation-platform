begin;

alter table ragapp.benchmark_datasets
  add column content_sha256 text;

alter table ragapp.benchmark_datasets disable trigger benchmark_datasets_reject_update;

update ragapp.benchmark_datasets
set content_sha256 = encode(digest(content::text, 'sha256'), 'hex')
where content_sha256 is null;

alter table ragapp.benchmark_datasets enable trigger benchmark_datasets_reject_update;

alter table ragapp.benchmark_datasets
  alter column content_sha256 set not null,
  add constraint benchmark_datasets_content_sha256_check
    check(content_sha256 ~ '^[0-9a-f]{64}$');

create index benchmark_datasets_project_created_idx
  on ragapp.benchmark_datasets(project_id, created_at desc);

create unique index benchmark_datasets_project_name_version_idx
  on ragapp.benchmark_datasets(project_id, lower(name), version);

create unique index benchmark_datasets_project_name_content_idx
  on ragapp.benchmark_datasets(project_id, lower(name), content_sha256);

commit;
