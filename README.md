# RAG Experimentation and Evaluation System

A workspace for building, testing, and using retrieval-augmented generation (RAG) systems.

The platform turns project documents into searchable vector indexes, tests RAG configurations against benchmark questions, and promotes a successful experiment into an assistant. Every execution records its configuration, inputs, outputs, and timing so results can be inspected and compared.

This is an active prototype built to explore practical, production-minded RAG engineering.

## Platform components

Each account starts with a default project. A project keeps the following components together:

- **Knowledge Base** stores versioned source documents and folders.
- **Indexes** turn selected documents into chunks and vector embeddings.
- **Prompts** store versioned system, RAG answer, and evaluation prompts.
- **Benchmarks** store questions and expected answers for consistent testing.
- **Experiments** combine an index, prompts, retrieval settings, and generation settings into testable variants.
- **Assistants** are created from completed experiment runs and retain the tested configuration.
- **Runs** provides project-wide execution history, timings, errors, traces, and lineage.
- **Project settings** controls project details, members, and feature-level permissions.

## How the components work together

1. Documents are uploaded to the Knowledge Base.
2. An index selects documents or folders from that knowledge base.
3. The worker partitions the documents, creates chunks, and generates embeddings.
4. Prompts and benchmark questions are prepared for testing.
5. An experiment variant references the index, prompt versions, retrieval settings, and Gemini model settings.
6. The variant runs against the benchmark and records answers, retrieved context, metrics, and latency.
7. A completed run can be promoted into an assistant.
8. The assistant playground uses the promoted configuration to answer questions from its selected index.

This separation makes it possible to change one part of a RAG system without overwriting another. Variants can share a benchmark while using different indexes, prompts, or generation settings.

## Architecture

### Web application

The interface uses Next.js, React, and TypeScript. Next.js server routes sit between the browser and the backend API. They keep authentication tokens in secure cookies and attach access tokens to backend requests without exposing them to client-side code.

This boundary keeps authentication handling in one place and allows project data to load on the server before a page is rendered.

### API and application modules

The backend is a FastAPI modular monolith. Authentication, projects, knowledge, indexing, prompts, benchmarks, experiments, assistants, and lineage have separate application modules inside one deployable service.

This keeps the system simple to run while preserving clear feature boundaries. Shared behavior is expressed through contracts, while Gemini, PostgreSQL, object storage, and document processing remain replaceable integrations.

Pydantic validates API input and runtime settings. Production refuses to start when required database, authentication, invitation, or CORS settings are unsafe.

### Background worker

Document ingestion, index creation, and experiment evaluation run outside the API request cycle. Work is stored in PostgreSQL and claimed by a Python worker using statuses, priorities, attempts, and leases.

Leases allow abandoned work to be recovered if a worker stops. Unique active-job rules prevent the same stage from running twice for one source or index specification. Experiment cases are resumable, so a failed run does not need to repeat completed cases.

### AI and document processing

The Unstructured API partitions documents into elements while preserving useful page and layout metadata. The ingestion pipeline turns those elements into chunks and records which elements contributed to each chunk.

Google Gemini provides embeddings, answer generation, and evaluation. HTTP clients are reused, query embeddings are cached within a run, context size is bounded, and provider concurrency is limited. These controls reduce connection overhead, repeated model calls, latency, and accidental quota exhaustion.

### Storage

Uploaded documents and extracted assets use local storage during development and Cloudflare R2-compatible object storage in production. PostgreSQL stores their identities, versions, hashes, metadata, and relationships instead of storing large files directly in relational tables.

This keeps metadata transactional while allowing file storage to scale independently.

## PostgreSQL and pgvector

PostgreSQL is the system of record for users, projects, permissions, documents, configurations, jobs, experiments, assistants, and lineage. It provides the transactions and relational consistency needed by the platform while also supporting vector search through pgvector.

pgvector stores chunk embeddings beside the chunks and their metadata. Retrieval can apply project and index boundaries before returning results without maintaining a separate vector database and synchronization process.

The database uses different index types for different access patterns:

- **B-tree indexes** support project, resource, status, and time-based queries. They keep workspace pages, run history, document versions, messages, and audit history efficient as records grow.
- **Composite indexes** match common access patterns such as project plus creation time, knowledge base plus source version, or conversation plus message time.
- **Partial indexes** include only active or actionable rows. They improve queries for non-deleted resources, pending jobs, running leases, and unaccepted invitations without indexing unnecessary historical rows.
- **Unique indexes** enforce rules such as one active email, one active prompt name within a project, one benchmark version, one artifact identity, and one active pipeline stage.
- **GIN full-text indexes** index the search vector stored with every chunk and support keyword retrieval alongside semantic retrieval.
- **HNSW vector indexes** provide approximate nearest-neighbour search over chunk embeddings. They use the dimensions and distance operator of the associated embedding model or immutable index specification.

HNSW avoids scanning every stored embedding for each query. Keeping vector indexes specification-aware prevents embeddings created by different models or dimensions from being mixed accidentally.

PostgreSQL connection pools are shared by API and asynchronous workflows. Reusing connections avoids opening a new database connection for every request and places a clear limit on database concurrency.

## Data integrity and lineage

Configurations are stored as immutable specifications with canonical hashes. Documents, chunks, embeddings, benchmark versions, prompt versions, and other outputs are registered as artifacts. Executions connect those artifacts as ordered inputs and outputs.

Foreign keys include project identity where necessary, preventing resources from one project from being linked to another. Database constraints and triggers protect immutable records and valid execution state changes even if an application code path is incorrect.

Content hashes provide deterministic identity for configurations and artifacts. Idempotency indexes prevent the same logical execution from being created more than once.

The result is a traceable path from an assistant response back to the experiment, index, chunks, and source documents that produced it.

## Authentication and project access

Passwords are hashed with Argon2id. Access tokens are short-lived, while refresh tokens are stored as hashes and rotated after use. Reusing a revoked refresh token invalidates its token family.

Production account creation requires an invitation code. Registration and login use database-backed rate limits that work across API instances without storing raw IP addresses.

Project roles and feature-level permissions are checked by the backend. The owner retains all privileges, while invited members can receive narrower access to knowledge, indexes, experiments, assistants, runs, or settings.

## Deployment

Docker Compose runs PostgreSQL, the API, and the worker locally. Production images are built by GitHub Actions, stored in Amazon ECR, and deployed to EC2.

Database migrations run before the API and worker restart. Production containers use read-only filesystems, drop Linux capabilities, and run with `no-new-privileges`. Images are tagged with the Git commit so deployed code can be traced to repository history.

## Start the services:

```bash
cd apps/backend
docker compose up --build -d
```

Apply pending migrations:

```bash
docker compose run --rm api ragapp-migrate
```

Check migration status:

```bash
docker compose run --rm api ragapp-migrate --status
```

### Frontend

Create `apps/frontend/.env.local`:

```dotenv
BACKEND_API_URL=http://localhost:8000
APP_VERSION=2.0.0
```

Start the frontend:

```bash
cd apps/frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Useful commands

Run backend tests:

```bash
cd apps/backend
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Run frontend checks:

```bash
cd apps/frontend
pnpm typecheck
pnpm lint
pnpm build
```

View backend health and API documentation:

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## License

This project is source-available for portfolio review and demonstration purposes. It is not open source. See [LICENSE](LICENSE) for details.
