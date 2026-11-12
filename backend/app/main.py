from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gm_auth import create_auth_router

from app.config import get_settings
from app.auth import auth_service, bootstrap_admin
from app.product_api import router as product_router
from app.reminders import followup_push_loop
from app.drive_backup import business_snapshot_loop

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_admin()
    worker = asyncio.create_task(followup_push_loop())
    snapshot_worker = asyncio.create_task(business_snapshot_loop())
    try:
        yield
    finally:
        worker.cancel()
        snapshot_worker.cancel()
        try:
            await asyncio.gather(worker, snapshot_worker)
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Drive-Status"],
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
    from sqlalchemy import inspect, text

    schema_revision = "unknown"
    try:
        with auth_service.engine.connect() as connection:
            if inspect(connection).has_table("alembic_version"):
                revisions = sorted(connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all())
                schema_revision = ",".join(revisions) if revisions else "unknown"
    except Exception:
        schema_revision = "unknown"
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "commit_sha": settings.source_commit,
        "schema_revision": schema_revision,
    }


@app.get("/health/ready")
def ready() -> dict[str, str]:
    from app.database import check_database_connection
    check_database_connection(auth_service.engine)
    return {"service": settings.app_name, "status": "ready", "environment": settings.app_env}
