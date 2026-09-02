begin;

alter table ragapp.prompts
  add column origin text not null default 'custom',
  add column preset_key text;

alter table ragapp.prompts
  add constraint prompts_origin_check check (origin in ('preinstalled', 'custom')),
  add constraint prompts_preset_identity_check check (
    (origin = 'preinstalled' and preset_key is not null)
    or (origin = 'custom' and preset_key is null)
  );

create unique index prompts_project_preset_idx
  on ragapp.prompts(project_id, preset_key)
  where preset_key is not null;

create table ragapp.prompt_presets (
  preset_key text primary key,
  name text not null,
  purpose text not null,
  description text not null,
  prompt_type text not null,
  template text not null,
  variables jsonb not null,
  display_order integer not null,
  check(prompt_type in ('system', 'rag_answer', 'evaluation')),
  check(jsonb_typeof(variables) = 'array')
);

insert into ragapp.prompt_presets
  (preset_key, name, purpose, description, prompt_type, template, variables, display_order)
values
  (
    'system_grounded_assistant',
    'Grounded knowledge assistant',
    'assistant_behavior',
    'Keeps the assistant factual, transparent and limited to available evidence.',
    'system',
    'You are a grounded knowledge assistant. Answer using the evidence made available to you. Do not invent facts or sources. If the evidence is insufficient, state that clearly. Distinguish facts from assumptions and keep the response direct and useful.',
    '[]'::jsonb,
    10
  ),
  (
    'system_concise_assistant',
    'Concise knowledge assistant',
    'assistant_behavior',
    'Produces brief, professional responses while preserving factual accuracy.',
    'system',
    'You are a concise, professional knowledge assistant. Lead with the answer, use plain language and include only details that help the user. Never claim that the supplied evidence says something it does not say. Say when information is unavailable.',
    '[]'::jsonb,
    20
  ),
  (
    'rag_grounded_answer',
    'Grounded answer',
    'answer_generation',
    'Answers a question strictly from retrieved context and acknowledges missing evidence.',
    'rag_answer',
    E'Answer the question using only the context below. If the context is insufficient, say that you do not have enough information. Do not use unsupported prior knowledge.\n\nContext:\n{{context}}\n\nQuestion:\n{{question}}\n\nAnswer:',
    '["context", "question"]'::jsonb,
    30
  ),
  (
    'rag_cited_answer',
    'Grounded answer with citations',
    'answer_generation',
    'Produces an evidence-grounded answer and preserves source references present in the context.',
    'rag_answer',
    E'Use only the supplied context to answer the question. Cite the relevant source reference after each supported claim using the reference exactly as it appears in the context. If the answer is not supported, say so explicitly.\n\nContext:\n{{context}}\n\nQuestion:\n{{question}}\n\nAnswer with citations:',
    '["context", "question"]'::jsonb,
    40
  ),
  (
    'evaluation_context_precision',
    'Context precision evaluator',
    'context_precision',
    'Scores how much of the retrieved context is relevant to answering the question.',
    'evaluation',
    E'Evaluate the precision of the retrieved context for the question. Determine what proportion of the retrieved information is relevant and useful. Return only JSON with keys score (number from 0 to 1), reason (short string), and irrelevant_context (array of short strings).\n\nQuestion:\n{{question}}\n\nRetrieved context:\n{{context}}',
    '["context", "question"]'::jsonb,
    100
  ),
  (
    'evaluation_context_recall',
    'Context recall evaluator',
    'context_recall',
    'Scores whether retrieved context contains the evidence required by the reference answer.',
    'evaluation',
    E'Evaluate whether the retrieved context contains all evidence needed to support the reference answer. Return only JSON with keys score (number from 0 to 1), reason (short string), and missing_evidence (array of short strings).\n\nQuestion:\n{{question}}\n\nRetrieved context:\n{{context}}\n\nReference answer:\n{{reference_answer}}',
    '["context", "question", "reference_answer"]'::jsonb,
    110
  ),
  (
    'evaluation_faithfulness',
    'Faithfulness evaluator',
    'faithfulness',
    'Scores whether every claim in an answer is supported by the retrieved context.',
    'evaluation',
    E'Evaluate whether every factual claim in the answer is supported by the context. Do not judge writing style. Return only JSON with keys score (number from 0 to 1), reason (short string), and unsupported_claims (array of short strings).\n\nContext:\n{{context}}\n\nAnswer:\n{{answer}}',
    '["answer", "context"]'::jsonb,
    120
  ),
  (
    'evaluation_answer_relevance',
    'Answer relevance evaluator',
    'answer_relevance',
    'Scores how directly and completely the answer addresses the question.',
    'evaluation',
    E'Evaluate how directly and completely the answer addresses the question. Ignore factual correctness unless it affects relevance. Return only JSON with keys score (number from 0 to 1), reason (short string), and omissions (array of short strings).\n\nQuestion:\n{{question}}\n\nAnswer:\n{{answer}}',
    '["answer", "question"]'::jsonb,
    130
  ),
  (
    'evaluation_hallucination',
    'Hallucination evaluator',
    'hallucination_detection',
    'Detects claims that cannot be verified from the retrieved context.',
    'evaluation',
    E'Identify claims in the answer that are not supported by the context. A lower score means more hallucination. Return only JSON with keys score (number from 0 to 1), reason (short string), and hallucinated_claims (array of short strings).\n\nContext:\n{{context}}\n\nAnswer:\n{{answer}}',
    '["answer", "context"]'::jsonb,
    140
  );

create function ragapp.install_default_prompts(target_project_id uuid, actor_id uuid)
returns void
language plpgsql
as $$
declare
  preset ragapp.prompt_presets%rowtype;
  new_prompt_id uuid;
begin
  for preset in
    select * from ragapp.prompt_presets order by display_order
  loop
    insert into ragapp.prompts (
      project_id, name, purpose, description, prompt_type,
      origin, preset_key, created_by
    ) values (
      target_project_id, preset.name, preset.purpose, preset.description,
      preset.prompt_type, 'preinstalled', preset.preset_key, actor_id
    )
    on conflict (project_id, preset_key) where preset_key is not null do nothing
    returning id into new_prompt_id;

    if new_prompt_id is not null then
      insert into ragapp.prompt_versions (
        prompt_id, project_id, version, template, variables,
        content_sha256, change_note, created_by
      ) values (
        new_prompt_id, target_project_id, 1, preset.template, preset.variables,
        encode(digest(trim(preset.template), 'sha256'), 'hex'),
        'Preinstalled project prompt', actor_id
      );
    end if;

    new_prompt_id := null;
  end loop;
end;
$$;

create function ragapp.install_default_prompts_for_project()
returns trigger
language plpgsql
as $$
begin
  perform ragapp.install_default_prompts(new.id, new.owner_id);
  return new;
end;
$$;

create trigger projects_install_default_prompts
after insert on ragapp.projects
for each row execute function ragapp.install_default_prompts_for_project();

do $$
declare
  project record;
begin
  for project in select id, owner_id from ragapp.projects loop
    perform ragapp.install_default_prompts(project.id, project.owner_id);
  end loop;
end;
$$;

commit;
