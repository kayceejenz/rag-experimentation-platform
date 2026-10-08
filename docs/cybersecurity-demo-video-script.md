# Small Business Cybersecurity — Demo Video Script

## Demo objective

Show how the platform turns trusted documents into a tested, traceable RAG assistant. The key message is not simply “upload documents and chat.” It is:

> We build an immutable retrieval pipeline, evaluate competing configurations against a versioned benchmark, and promote a successful experiment into an assistant with end-to-end lineage.

Target length: **10–12 minutes**.

Demo account: `admin@app.com`

Project: **Small Business Cybersecurity**

## Before recording

- Log in and select **Small Business Cybersecurity**.
- Close unrelated browser tabs and hide developer tools.
- Use browser zoom around 90–100%, ensuring the project navigation and detail panels fit.
- Confirm the index and both experiment runs still show `Ready`/`Completed`.
- Open the assistant in a fresh conversation before recording.
- Avoid starting a new experiment run during the recording; the saved completed runs tell the story without provider latency.
- Use one supported question and one deliberate missing-information question in the live assistant:
  - `What are the six functions of NIST CSF 2.0?`
  - `What is our company’s annual cybersecurity budget?`

## Storyline at a glance

```text
Project boundary
  → Knowledge Base: source documents and versions
  → Index: partitioning, chunking and vector embeddings
  → Prompts: versioned system, answer and evaluator instructions
  → Benchmark: fixed questions and reference answers
  → Experiment: controlled retrieval variants
  → Runs: case-level metrics, traces and comparison
  → Assistant: promoted immutable revision
  → Chat: retrieval, grounded generation and citations
```

## 1. Opening and project overview — 45 seconds

### On screen

Log in as `admin@app.com`, select **Small Business Cybersecurity**, and begin on the project overview.

### Say

“This is a RAG experimentation and evaluation platform. I’m going to demonstrate the full lifecycle using our Small Business Cybersecurity project: from source documents, through indexing and controlled evaluation, to a production-style assistant.

The project is the primary workspace and security boundary. Knowledge, indexes, prompts, benchmarks, experiments, and assistants are all project-scoped, which prevents assets from being accidentally linked across projects and allows access to be controlled by feature-level permissions.

The important distinction is that an assistant is not created directly from a folder of documents. It is promoted from a tested experiment configuration, so we can explain exactly which sources, index, prompts, retrieval settings, and model produced it.”

### Transition

“The lifecycle starts with the evidence the assistant is allowed to use.”

## 2. Knowledge Base — 1 minute 20 seconds

### On screen

Open **Knowledge Base**. Show the three folders, then the four documents and one document preview if it opens quickly.

Current data:

- **Foundations**
  - `NIST.SP.1300.pdf` — 88 chunks
  - `NIST.CSWP.29.pdf` — 172 chunks
- **Incident Response**
  - `StopRansomware-Guide 508.pdf` — 152 chunks
- **Supplier Security**
  - `Securing-SMB-Supply-Chains_Resource-Handbook_508.pdf` — 92 chunks

### Say

“The Knowledge Base is the source-of-truth layer. Here I have organised four authoritative cybersecurity PDFs into Foundations, Incident Response, and Supplier Security.

The system separates a **source** from a **source version**. The source is the logical document identity; a source version is the immutable uploaded file, with its filename, media type, checksum, object-storage key, and processing state. That means a document can evolve without erasing the exact file used by an earlier experiment.

Folders are not only visual organisation. They can also define index scope, allowing a retrieval pipeline to include the knowledge-base root or selected folders.

The binary files live in object storage, while PostgreSQL stores the document metadata, processing state, and relationships. This keeps large files out of the transactional database while preserving traceability.”

### Technical terms to emphasise

- Logical source identity
- Immutable source version
- Content checksum
- Object storage
- Project-scoped metadata
- Index scope

### Transition

“Documents are useful to people, but retrieval needs a searchable numerical representation. That is the job of the index pipeline.”

## 3. Indexes — 1 minute 30 seconds

### On screen

Open **Indexes**, select **Cybersecurity Baseline**, and show its configuration and ready state.

Current configuration:

- Partitioning provider: **Unstructured**
- Strategy: `auto`
- PDF strategy: `hi_res`
- OCR language: English
- Chunking strategy: `by_title`
- Embedding provider: **Gemini**
- Embedding model: `gemini-embedding-2`
- Dimensions: `768`
- Result: **504 chunks**

### Say

“This is the Cybersecurity Baseline index. An index is an immutable pipeline specification rather than just a collection of vectors.

First, Unstructured partitions each PDF into semantic elements while preserving useful document metadata such as page and layout information. The `hi_res` PDF strategy is intended to retain structure from more complex PDFs.

Next, the `by_title` chunking strategy groups related elements around document headings. That is a better semantic boundary than cutting text at arbitrary character counts.

Each chunk is then converted into a 768-dimensional vector using Gemini’s embedding model. PostgreSQL with pgvector stores those embeddings alongside the relational metadata. At query time, the user’s question is embedded with the same model and nearest-neighbour vector search finds semantically similar chunks.

This build produced 504 searchable chunks across the four documents. Because the pipeline specification is immutable and content-addressed, we can later compare a different chunking or embedding strategy without mutating this baseline.”

### Optional deeper point

“The worker performs partitioning, chunking, and embedding asynchronously. Jobs are durable database records with leases and retry state, so a failed worker can be recovered without silently losing the task.”

### Technical terms to emphasise

- Partitioning
- Semantic elements
- Chunking strategy
- Embedding vector
- Vector dimensionality
- Nearest-neighbour search
- pgvector
- Immutable pipeline specification
- Background worker and durable job

### Transition

“The index controls what evidence can be retrieved. Prompts control how that evidence is interpreted and how the answer is produced.”

## 4. Prompts — 1 minute 20 seconds

### On screen

Open **Prompts**. Filter or point out the three types: System, RAG answer, and Evaluation. Open these examples:

- **Cybersecurity Guide** — custom system prompt
- **Document-Grounded Cybersecurity Answer** — custom RAG-answer prompt
- **Context precision evaluator** — preinstalled evaluator with versions 1 and 2

Note: the saved experiment variants currently use **Concise knowledge assistant v1** as the system prompt and **Document-Grounded Cybersecurity Answer v1** as the RAG prompt.

### Say

“Prompts are managed as reusable, versioned assets. The parent prompt stores its identity, type, purpose, and status. The actual template lives in an immutable prompt version.

There are three prompt types. A **system prompt** defines global assistant behaviour and boundaries. A **RAG-answer prompt** combines the user question with retrieved context; its `context` and `question` variables are validated before it can be saved. **Evaluation prompts** act as LLM judges for metrics such as faithfulness, answer relevance, context recall, and context precision.

Experiments reference exact prompt-version IDs rather than ‘the latest prompt.’ This prevents a later edit from silently changing an old result or a deployed assistant.

The preinstalled prompts are copied from a preset library when a project is created, after which they are project-owned assets. Custom prompts can then be added for the domain. Here, our answer prompt explicitly requires document-grounded answers and supplied citation labels.”

### Technical terms to emphasise

- Prompt registry
- Immutable version
- Template variables
- System instruction
- RAG answer template
- LLM-as-a-judge evaluator
- Reproducibility

### Transition

“Once retrieval and generation are configurable, we need a stable test set so that we compare variants against the same questions.”

## 5. Benchmarks — 1 minute 10 seconds

### On screen

Open **Benchmarks** and select **Small Business Security Questions**, version 1. Show several of its 10 cases.

Recommended cases to highlight:

- “What are the six functions of NIST CSF 2.0?”
- “Which accounts should a small business prioritise for MFA?”
- “How do Respond and Recover differ?”
- “What is our company’s annual cybersecurity budget?”

### Say

“This benchmark is a versioned evaluation dataset containing ten cases. Each case has a stable ID, a question, a reference answer, optional expected context, and tags.

The cases test more than simple fact lookup. Some require synthesising evidence across sections. Two are deliberate missing-information checks. For example, the uploaded public guidance cannot know our company’s annual cybersecurity budget. A safe assistant should acknowledge that limitation rather than invent a number.

Versioning and hashing the benchmark means every variant in a run is evaluated against exactly the same frozen cases. That gives us a controlled comparison rather than an informal chat demonstration.”

### Technical terms to emphasise

- Evaluation dataset
- Golden/reference answer
- Expected context
- Stable case ID
- Negative or missing-information test
- Dataset versioning
- Controlled comparison

### Transition

“With a fixed index, prompts, model, and benchmark, we can isolate one variable and test a hypothesis.”

## 6. Experiments and variants — 1 minute 20 seconds

### On screen

Open **Experiments**, select **Cybersecurity Retrieval Comparison**, and show the hypothesis and both variants.

Hypothesis:

> Retrieving more chunks may improve completeness, but could introduce irrelevant context and increase latency.

Controlled variables:

- Same index: Cybersecurity Baseline
- Same generation model: `gemini-3.5-flash-lite`
- Same temperature: `0.2`
- Same maximum output: `2048` tokens
- Same prompts and benchmark

Independent variable:

- **Baseline Retrieval:** `top_k = 3`
- **Expanded Retrieval:** `top_k = 6`

### Say

“An experiment is the named comparison, while a variant is one immutable, testable RAG configuration.

The hypothesis is that retrieving more chunks may improve completeness, but may also introduce irrelevant context and increase latency. To isolate that effect, both variants use the same index, generation model, temperature, prompt versions, and benchmark. The primary change is retrieval depth: top K of three versus top K of six.

Each variant receives a deterministic configuration hash based on its canonical configuration. This prevents duplicate configurations and gives logically identical settings a stable identity.

The experiment evaluates answer relevance, context precision, context recall, and faithfulness, with faithfulness as the primary metric.”

### Explain the metrics clearly

- **Faithfulness:** Are the answer’s factual claims supported by retrieved context?
- **Answer relevance:** Does the answer directly address the question?
- **Context recall:** Did retrieval find the evidence needed for the reference answer?
- **Context precision:** How much of the retrieved context was actually relevant?

### Transition

“Now we can inspect the empirical result instead of choosing a configuration by intuition.”

## 7. Runs, results, and traces — 1 minute 45 seconds

### On screen

Open the completed runs or the Runs module. Show the aggregate results, then open one case if convenient.

Saved results:

| Variant | Faithfulness | Context recall | Answer relevance | Context precision |
|---|---:|---:|---:|---:|
| Baseline Retrieval | 1.000 | 1.000 | 0.980 | 0.475 |
| Expanded Retrieval | 1.000 | 1.000 | 0.980 | 0.535 |

### Say

“Both variants completed all ten benchmark cases. Faithfulness and context recall are 1.0 for both, and answer relevance is 0.98. Expanded Retrieval improves aggregate context precision from 0.475 to 0.535.

So the extra retrieval depth did not damage grounding or recall in this run, and it produced a modest precision improvement. This is important: a larger top K does not automatically mean better retrieval. It has to be measured because additional chunks can add noise, increase context size, and affect latency.

The platform stores results per benchmark case, not only as a final average. A trace includes the retrieved context, generated answer, evaluator outputs, token count, and stage-level latency for embedding, vector search, context assembly, generation, and evaluation. Aggregate metrics help us compare variants; case-level traces help us diagnose why a score changed.

For the missing-information budget question, the generated response correctly states that the information is unavailable. That demonstrates grounded abstention: the model refuses to turn general cybersecurity guidance into a fabricated company fact.”

### Important nuance to say accurately

“These scores support the choice for this benchmark and this dataset; they are not a universal guarantee of quality or security.”

### Technical terms to emphasise

- Variant run
- Case-level result
- Aggregate metric
- Retrieval trace
- Operational telemetry
- Stage-level latency
- Grounded abstention
- Resumable execution

### Transition

“Once a variant has evidence behind it, we can promote that tested configuration into an assistant.”

## 8. Assistant promotion and lineage — 1 minute 10 seconds

### On screen

Open **Assistants**, select **CyberSecurity Assistant**, and show revision/lineage details.

Current assistant:

- Name: **CyberSecurity Assistant**
- Status: Active
- Active revision: v1
- Promoted from: **Expanded Retrieval** completed variant run
- Retrieval: `top_k = 6`, `min_score = 0.0`
- Model: `gemini-3.5-flash-lite`
- Temperature: `0.2`

### Say

“This assistant was promoted from the completed Expanded Retrieval variant run. Promotion creates an immutable assistant revision containing the tested index reference, exact prompt-version IDs, retrieval settings, generation settings, and source variant-run lineage.

That snapshot is the deployment boundary. If someone later creates a new prompt version or another index, the active assistant does not silently change. A new tested configuration can instead become a new revision.

The lineage view connects the live assistant back to the experiment, run, variant, prompt versions, index specification, chunks, and source documents. That gives us auditability and reproducibility rather than an opaque chatbot configuration.”

### Technical terms to emphasise

- Promotion
- Immutable assistant revision
- Configuration snapshot
- Active revision
- Lineage/provenance
- Auditability

### Transition

“Finally, let’s see what that promoted configuration does at runtime.”

## 9. Live assistant demonstration — 1 minute 30 seconds

### On screen and say

Start a fresh conversation.

#### Question 1: supported fact

Ask:

> What are the six functions of NIST CSF 2.0?

While the answer streams, say:

“At runtime, the question is embedded with the same embedding model used by the selected index. pgvector performs semantic nearest-neighbour retrieval within that exact index specification. The highest-scoring chunks are assembled into a bounded context, rendered into the versioned RAG prompt, and sent to Gemini with the system instruction. The answer streams back to the user, and citations map to the retrieved source chunks.”

After the response, open or point out the citations/source panel:

“These are evidence links, not model-generated bibliography entries. They are derived from the source and page metadata attached to the retrieved chunks.”

#### Question 2: unsupported company fact

Ask:

> What is our company’s annual cybersecurity budget?

After the response, say:

“The public guidance contains no company budget. The expected behaviour is to state that limitation clearly. This is as important as answering supported questions: a grounded assistant must distinguish recommendations in its sources from facts about the user’s organisation.”

### Technical terms to emphasise

- Query embedding
- Semantic retrieval
- Bounded context assembly
- Prompt rendering
- Streaming generation
- Chunk-derived citation
- Grounding
- Abstention

## 10. Closing — 35 seconds

### Say

“That completes the lifecycle: versioned documents become a reproducible vector index; versioned prompts and benchmarks define how configurations are tested; experiment runs produce case-level evidence; and a successful variant becomes an immutable assistant revision.

The central value is controlled change. We can improve documents, chunking, embeddings, prompts, retrieval settings, or models independently, compare the result against a stable benchmark, and promote only the configuration we intend to run. Every assistant answer remains connected to the tested configuration and original evidence behind it.”

## Shorter 6-minute cut

If the recording must be shorter:

1. Opening/project boundary — 30 seconds
2. Knowledge Base — 45 seconds
3. Index — 60 seconds
4. Prompts + Benchmark together — 60 seconds
5. Experiment + Runs — 90 seconds
6. Assistant + one live supported question — 90 seconds
7. Closing — 25 seconds

Skip document preview, evaluator prompt internals, the second live question, and the detailed worker explanation.

## Presenter vocabulary cheat sheet

| Avoid saying | Prefer |
|---|---|
| “The PDF is put into the AI” | “The document version is partitioned, chunked, embedded, and indexed.” |
| “The database searches the words” | “pgvector performs semantic nearest-neighbour retrieval over query and chunk embeddings.” |
| “We trained the model on our PDFs” | “We use retrieval-augmented generation; the foundation model is not retrained.” |
| “This prompt gets edited” | “A new immutable prompt version is created.” |
| “The AI checks the AI” | “Versioned evaluator prompts implement LLM-as-a-judge metrics.” |
| “This is the best configuration” | “This variant performed best for this benchmark and dataset.” |
| “The assistant uses the experiment” | “The assistant runs an immutable revision promoted from a completed variant run.” |
| “The citations come from Gemini” | “Citations are derived from retrieved chunks and their source metadata.” |
| “The score proves it is correct” | “The score is evidence from a defined benchmark and should be interpreted with case-level traces.” |

## Recording cautions

- Do not say the model was fine-tuned or trained on the documents; this is RAG.
- Do not claim that a 1.0 evaluator score guarantees factual correctness outside the benchmark.
- Do not claim top K 6 is universally superior; it performed better on aggregate context precision in these saved runs.
- Do not describe evaluation prompts as deterministic rules; they are model-based judges whose outputs should be inspected.
- Do not imply that citations prove an entire answer automatically; they identify the retrieved evidence associated with supported claims.
- The experiment used **Concise knowledge assistant v1**, even though **Cybersecurity Guide** is also present as a custom system prompt.
- The context-precision evaluator was later given a v2, but the saved variants reference v1. This is a useful demonstration of why exact version IDs preserve historical reproducibility.
