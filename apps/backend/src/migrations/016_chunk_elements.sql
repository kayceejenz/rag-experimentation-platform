begin;

create table ragapp.chunk_elements (
 chunk_id uuid not null references ragapp.chunks(id) on delete cascade,
 source_element_id uuid not null references ragapp.source_elements(id) on delete cascade,
 element_order integer not null, 
 primary key(chunk_id,source_element_id), 
 unique(chunk_id,element_order), 
 check(element_order>=0)
);

create index chunk_elements_element_idx on ragapp.chunk_elements(source_element_id);
commit;
