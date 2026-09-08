# RAG Experimentation and Evaluation System

A workspace for building and evaluating retrieval-augmented generation (RAG) systems.

The system takes documents through indexing, evaluation, and deployment as a traceable AI assistant. It is an active prototype focused on practical RAG engineering workflows.

Each project contains:

- **Knowledge Base**: source documents and folders.
- **Indexes**: chunked and embedded versions of selected documents.
- **Prompts**: versioned system, answer, and evaluation prompts.
- **Benchmarks**: test questions and expected answers.
- **Experiments**: configurations and evaluation runs.
- **Assistants**: tested configurations promoted for use.
- **Runs**: execution history, traces, and lineage.

## Using the platform

### 1. Create a project

Register an account and open the default project. A project keeps its knowledge, experiments, assistants, members, and permissions together.

### 2. Add knowledge

Open **Knowledge Base** and upload documents. Documents can be organized into folders and previewed within the application.

### 3. Build an index

Open **Indexes**, select the documents or folders to include, and choose:

- A chunking strategy
- An embedding model
- The required model dimensions

The worker creates the chunks and vector embeddings. Index artifacts and stage timings can be inspected after the build completes.

### 4. Prepare an experiment

Before creating an experiment:

1. Add or select versioned prompts.
2. Create a benchmark dataset with test questions.
3. Create an experiment and one or more variants.

A variant binds an index, prompts, retrieval settings, and generation settings into one testable configuration.

### 5. Run and evaluate

Run a selected variant against a benchmark dataset. The result includes generated answers, retrieved context, evaluation metrics, and latency measurements.

Variants can be run independently and compared without rebuilding the underlying project assets.

### 6. Create an assistant

A completed experiment run can be promoted into an assistant. The assistant uses the exact index, prompts, retrieval settings, and model configuration recorded by that run.

Use the assistant **Playground** to start conversations. Use **Lineage** to inspect where its active configuration came from.

## Technology

| Layer               | Stack                      |
| ------------------- | -------------------------- |
| Frontend            | Next.js, React, TypeScript |
| API                 | FastAPI, Python, Pydantic  |
| Database            | PostgreSQL and pgvector    |
| Worker              | Python background worker   |
| AI provider         | Google Gemini              |
| Document processing | Unstructured API           |
| Local environment   | Docker Compose             |

## Repository structure

```text
apps/
├── backend/
│   ├── src/api/           API setup and dependencies
│   ├── src/integrations/  Database, model, and storage adapters
│   ├── src/migrations/    Forward-only SQL migrations
│   ├── src/modules/       Application modules
│   ├── src/worker.py      Background worker
│   └── tests/             Backend tests
└── frontend/
    └── src/
        ├── app/           Pages and API proxy routes
        ├── components/    Interface components
        ├── lib/           Auth, environment, and API utilities
        └── types/         Frontend data contracts
```

## Local setup

### Requirements

- Docker and Docker Compose
- Node.js 20 or newer
- pnpm
- Google Gemini API credentials
- Unstructured API credentials

### Backend

Create `apps/backend/.env`:

```dotenv
POSTGRES_DB=ragapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql://postgres:change-me@db:5432/ragapp

JWT_SECRET=replace-with-a-long-random-secret
APP_ENV=development
APP_REVISION=development
CORS_ORIGINS=http://localhost:3000

LLM_PROVIDER=gemini
LLM_MODEL=your-gemini-generation-model
LLM_API_KEY=your-gemini-api-key

EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=your-gemini-embedding-model
EMBEDDING_DIMENSIONS=768
EMBEDDING_API_KEY=your-gemini-api-key

UNSTRUCTURED_API_URL=your-unstructured-api-url
UNSTRUCTURED_API_KEY=your-unstructured-api-key
```

Start the services:

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
