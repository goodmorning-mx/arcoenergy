from pathlib import Path
import os
import re
import subprocess
import sys

from app.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_remote_contract() -> None:
    dockerfile = read("frontend/Dockerfile")
    nginx = read("frontend/nginx.conf")
    app = read("frontend/src/App.tsx")
    assert "WORKDIR /app" in dockerfile
    assert "RUN npm ci" in dockerfile
    assert "ARG VITE_API_URL" in dockerfile
    assert "ENV VITE_API_URL=$VITE_API_URL" in dockerfile
    version_script = read("frontend/write-version.sh")
    assert "COPY write-version.sh /docker-entrypoint.d/40-write-version.sh" in dockerfile
    assert 'commit_sha' in version_script and "${SOURCE_COMMIT:-unknown}" in version_script
    assert "RUN npm run build" in dockerfile
    assert "FROM nginx:" in dockerfile
    assert "EXPOSE 80" in dockerfile
    assert "HEALTHCHECK" in dockerfile and "http://127.0.0.1/" in dockerfile
    assert "ports:" not in dockerfile
    assert re.search(r"listen\s+80\s*;", nginx)
    assert "try_files $uri $uri/ /index.html;" in nginx
    assert "localhost:8000" not in nginx
    assert "import.meta.env.VITE_API_URL" in app


def test_backend_remote_contract() -> None:
    dockerfile = read("backend/Dockerfile")
    entrypoint = read("backend/entrypoint.sh")
    assert "FROM python:3.12-slim" in dockerfile
    assert 'alias="SOURCE_COMMIT"' in read("backend/app/config.py")
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "COPY alembic.ini ./" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile
    assert "chmod +x /app/entrypoint.sh" in dockerfile
    assert "USER app" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:8000/health" in dockerfile
    assert entrypoint.startswith("#!/bin/sh\nset -eu\n")
    assert "set -x" not in entrypoint
    assert "printenv" not in entrypoint and "env" not in entrypoint
    assert "DATABASE_URL" not in entrypoint
    assert "python -m app.migrations" in entrypoint
    assert "alembic upgrade head" not in entrypoint
    assert "exec uvicorn app.main:app --host 0.0.0.0 --port 8000" in entrypoint
    assert entrypoint.index("python -m app.migrations") < entrypoint.index("exec uvicorn")


def test_compose_local_contract() -> None:
    compose = read("compose.yaml")
    assert compose.startswith("# Local development only.")
    assert re.findall(r"^  (frontend|backend|postgres):", compose, re.MULTILINE) == [
        "frontend",
        "backend",
        "postgres",
    ]
    assert "context: ./frontend" in compose
    assert "VITE_API_URL:" in compose
    assert '"8080:80"' in compose
    assert "condition: service_healthy" in compose
    assert "build: ./backend" in compose
    assert '"8000:8000"' in compose
    assert "postgresql+psycopg://goodmorning:goodmorning_local_password@postgres:5432/goodmorning_mvp" in compose
    assert "image: postgres:16-alpine" in compose
    assert "postgres_data:/var/lib/postgresql/data" in compose
    assert "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}" in compose
    postgres_block = compose.split("\n  postgres:", 1)[1].split("\nvolumes:", 1)[0]
    assert "ports:" not in postgres_block
    forbidden = ["traefik", "docker_compose_domains", "ssh", "rsync", "scp"]
    assert not any(term in compose.lower() for term in forbidden)


def test_alembic_infrastructure_and_safe_database_url_handling() -> None:
    env = read("backend/alembic/env.py")
    ini = read("backend/alembic.ini")
    assert (ROOT / "backend/alembic/script.py.mako").is_file()
    assert (ROOT / "backend/alembic/versions").is_dir()
    assert "script_location = %(here)s/alembic" in ini
    assert "sqlalchemy.url" not in ini
    assert "config.set_main_option" not in env
    assert "engine_from_config" not in env
    assert "create_engine(get_database_url(), poolclass=pool.NullPool)" in env
    assert 'config.attributes.get("connection")' in env
    assert "context.configure(\n        url=get_database_url()" in env
    migration_runner = read("backend/app/migrations.py")
    assert "pg_try_advisory_lock" in migration_runner
    assert "pg_advisory_unlock" in migration_runner
    assert 'command.upgrade(alembic_config(connection), "head")' in migration_runner
    versions = list((ROOT / "backend/alembic/versions").glob("*.py"))
    assert versions
    combined = "\n".join(path.read_text(encoding="utf-8") for path in versions)
    assert "create_table" not in combined


def test_template_reports_github_product_events_with_repository_oidc() -> None:
    workflow = read(".github/workflows/software-factory-events.yml")
    assert "workflow_run:" in workflow
    assert "pull_request:" in workflow
    assert "deployment_status:" in workflow
    assert "id-token: write" in workflow
    assert "software.goodmorning.mx" in workflow
    assert "https://api.dev.software.goodmorning.mx" in workflow
    assert "https://api.software.goodmorning.mx" in workflow
    assert "/internal/products/events" in workflow
    assert "repository_id" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "goodmorning-mvp-template" in workflow
    assert "'software'" in workflow
    assert "event === 'push'" in workflow
    assert "runtime-verification" in workflow
    assert "source SHA" in workflow
    assert "observed_sha" in workflow
    assert "attempt <= 36" in workflow
    assert "source_branch: sourceBranch" in workflow
    assert "source_event: sourceEvent" in workflow
    assert "source_workflow_name: sourceWorkflowName" in workflow
    assert not (ROOT / ".github/workflows/goodmorning-release.yml").exists()


def test_nextjs_runtime_version_endpoint_reads_coolify_source_commit() -> None:
    route = read("seo/app/version.json/route.ts")
    assert "force-dynamic" in route
    assert "process.env.SOURCE_COMMIT" in route
    assert "commit_sha" in route
    assert "Cache-Control" in route


def test_database_url_with_percent_encoded_password_is_accepted_without_output(monkeypatch, capsys) -> None:
    database_url = "postgresql+psycopg://gm:p%25ss%40word@db.internal:5432/gm?sslmode=require"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    assert get_settings().database_url == database_url
    captured = capsys.readouterr()
    assert database_url not in captured.out
    assert database_url not in captured.err
    get_settings.cache_clear()


def test_alembic_history_does_not_connect_or_print_database_url() -> None:
    database_url = "postgresql+psycopg://gm:p%25ss%40word@no-real-host.invalid:5432/gm"
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    result = subprocess.run(
        [sys.executable, "-c", "from alembic.config import main; main(argv=['-c', 'backend/alembic.ini', 'history', '--verbose'])"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    output = result.stdout + result.stderr
    assert "202607150001" in output
    assert database_url not in output
    assert "no-real-host.invalid" not in output


def test_documentation_separates_resource_variables_and_driver_contract() -> None:
    docs = read("docs/deployment.md") + read("README.md") + read(".env.example")
    assert "Frontend Application" in docs
    assert "Backend Application" in docs
    assert "native Coolify PostgreSQL" in docs or "PostgreSQL nativo" in docs
    assert "build-time" in docs
    assert "runtime" in docs
    assert "Local Docker Compose only" in docs
    assert "SQLAlchemy with psycopg 3" in docs
    assert "postgresql+psycopg://" in docs
    assert "converting only that initial scheme" in docs or "convierte solo ese esquema inicial" in docs
    assert "Do not copy every variable" in docs
    assert "DATABASE_URL must never" in docs


def test_no_real_secrets_production_identifiers_or_remote_operations() -> None:
    scanned_paths = [
        "compose.yaml",
        ".env.example",
        "README.md",
        "docs/deployment.md",
        "backend/app/config.py",
        "backend/alembic/env.py",
    ]
    scanned = "\n".join(read(path) for path in scanned_paths)
    forbidden_patterns = [
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
        r"ghp_[A-Za-z0-9_]{20,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}",
        r"postgres://[^\s:]+:[^\s@]*(?:prod|production)[^\s@]*@",
        r"coolify[_-]?[0-9a-f]{8}",
    ]
    for pattern in forbidden_patterns:
        assert re.search(pattern, scanned, flags=re.IGNORECASE) is None
    for term in ["ssh ", "rsync", "scp ", "docker -H", "DOCKER_HOST"]:
        assert term not in scanned.lower()
