import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.error_handlers import global_error_handler
from core.settings import Settings
from modules.auth.controllers.auth_controller import router as auth_router
from modules.chats.controllers.chat_controller import router as chat_router
from modules.knowledge_bases.controllers.knowledge_base_controller import router as kb_router
from modules.jobs.controllers.job_controller import router as job_router
from modules.projects.controllers.project_controller import router as project_router
from modules.sources.controllers.source_controller import router as source_router


def create_app() -> FastAPI:
    config = Settings()
    app = FastAPI(title="RagApp API", version="0.2.0", docs_url="/docs")
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

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ragapp-backend"}

    return app


app = create_app()


def run() -> None:
    config = Settings()
    uvicorn.run("api.main:app", host=config.api_host, port=config.api_port)
