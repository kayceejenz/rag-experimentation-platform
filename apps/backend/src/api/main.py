from contextlib import asynccontextmanager

import uvicorn
from api.error_handlers import global_error_handler
from core.settings import Settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from integrations.database import (
    close_database_pools,
    configure_database_pools,
    open_database_pools,
)
from integrations.http_client import close_http_clients
from modules.auth.controllers.auth_controller import router as auth_router
from modules.benchmarks.controller import router as benchmark_router
from modules.chats.controllers.chat_controller import router as chat_router
from modules.core.controllers.lineage_controller import router as lineage_router
from modules.experiments.controllers.experiment_controller import (
    router as experiment_router,
)
from modules.indexes.controllers.index_controller import router as index_router
from modules.jobs.controllers.job_controller import router as job_router
from modules.knowledge_bases.controllers.knowledge_base_controller import (
    router as kb_router,
)
from modules.knowledge_bots.controllers.knowledge_bot_controller import (
    router as knowledge_bot_router,
)
from modules.projects.controllers.project_controller import router as project_router
from modules.prompts.controllers.prompt_controller import router as prompt_router
from modules.sources.controllers.source_controller import router as source_router


def create_app() -> FastAPI:
    config = Settings()
    configure_database_pools(
        config.database_pool_min_size,
        config.database_pool_max_size,
        config.database_pool_timeout_seconds,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if config.database_url:
            await open_database_pools(config.database_url)
        yield
        await close_database_pools()
        await close_http_clients()

    app = FastAPI(
        title="RagApp API", version="0.2.0", docs_url="/docs", lifespan=lifespan
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    global_error_handler(app)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(project_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(kb_router, prefix="/api/v1")
    app.include_router(source_router, prefix="/api/v1")
    app.include_router(job_router, prefix="/api/v1")
    app.include_router(knowledge_bot_router, prefix="/api/v1")
    app.include_router(lineage_router, prefix="/api/v1")
    app.include_router(index_router, prefix="/api/v1")
    app.include_router(prompt_router, prefix="/api/v1")
    app.include_router(benchmark_router, prefix="/api/v1")
    app.include_router(experiment_router, prefix="/api/v1")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ragapp-backend"}

    return app


app = create_app()


def run() -> None:
    config = Settings()
    uvicorn.run("api.main:app", host=config.api_host, port=config.api_port)
