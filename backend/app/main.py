from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gm_auth import create_auth_router

from app.config import get_settings
from app.auth import auth_service, bootstrap_admin
from app.product_api import router as product_router
from app.seed import seed_inventory, seed_quote_catalog

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_admin()
    seed_inventory()
    seed_quote_catalog()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(create_auth_router(auth_service))
app.include_router(product_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "environment": settings.app_env,
    }


@app.get("/version")
def version() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "commit_sha": settings.source_commit,
    }


@app.get("/health/ready")
def ready() -> dict[str, str]:
    from app.database import check_database_connection
    check_database_connection(auth_service.engine)
    return {"service": settings.app_name, "status": "ready", "environment": settings.app_env}
