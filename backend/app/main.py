from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.health import router as health_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.middleware.api_key import api_key_middleware
from app.middleware.metrics import metrics_middleware
from app.routers.admin import router as admin_router
from app.routers.chat import router as chat_router
from app.services.seed import seed_default_data


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLMOps Gateway",
        description="Production-ready AI gateway and LLMOps platform.",
        version="0.1.0",
    )

    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
        seed_default_data()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(metrics_middleware)
    app.middleware("http")(api_key_middleware)

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.mount("/metrics", make_asgi_app())
    return app


app = create_app()
