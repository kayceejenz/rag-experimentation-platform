begin;

create table ragapp.knowledge_folders (
 id uuid primary key default gen_random_uuid(),
 knowledge_base_id uuid not null references ragapp.knowledge_bases(id) on delete cascade,
 parent_id uuid,
 name text not null,
 created_by uuid references ragapp.users(id) on delete set null,
 created_at timestamptz not null default now(),
 unique(id,knowledge_base_id),
 foreign key(parent_id,knowledge_base_id)
 references ragapp.knowledge_folders(id,knowledge_base_id) on delete cascade,
 check(length(trim(name)) between 1 and 160),
 check(parent_id is null or parent_id<>id)
);

create unique index knowledge_folders_sibling_name_idx
on ragapp.knowledge_folders(
 knowledge_base_id,coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid),lower(name)
);

alter table ragapp.sources add column folder_id uuid;
alter table ragapp.sources add constraint sources_folder_fk
foreign key(folder_id,knowledge_base_id)
references ragapp.knowledge_folders(id,knowledge_base_id) on delete restrict;
create index sources_folder_active_idx on ragapp.sources(knowledge_base_id,folder_id,created_at desc)
where deleted_at is null;

commit;
