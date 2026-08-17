begin;

create table ragapp.embedding_models (
 id uuid primary key default gen_random_uuid(), 
 provider text not null, 
 model_name text not null,
 dimensions integer not null, 
 distance_metric text not null default 'cosine', 
 configuration jsonb not null default '{}'::jsonb,
 is_active boolean not null default true, 
 created_at timestamptz not null default now(), 
 unique(provider,model_name,dimensions),
 check(dimensions between 1 and 16000), 
 check(distance_metric in ('cosine','l2','inner_product')),
 check(jsonb_typeof(configuration)='object')
);

commit;
