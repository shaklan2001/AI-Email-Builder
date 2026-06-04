from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, email, recipients, review, webhooks, workflows
from app.core.config import settings
from app.core.database import close_db, connect_db
from app.core.redis_client import ping_redis
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await connect_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Email Workflow Builder API",
        version="0.1.0",
        description="REST API for the AI Email Workflow Builder",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
    app.include_router(recipients.router, prefix="/api/v1/recipients", tags=["recipients"])
    app.include_router(review.router, prefix="/api/v1/review", tags=["review"])
    app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

    @app.get("/health")
    async def health() -> dict[str, str]:
        redis_ok = await ping_redis()
        return {
            "status": "ok",
            "redis": "connected" if redis_ok else "unavailable",
        }

    return app


app = create_app()
