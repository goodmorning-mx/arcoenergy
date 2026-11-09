from sqlalchemy import create_engine, text

from app import main


def test_version_reports_current_alembic_schema_revision(monkeypatch) -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(64) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version(version_num) VALUES ('202611090074')"))
    monkeypatch.setattr(main.auth_service, "engine", engine)

    assert main.version()["schema_revision"] == "202611090074"
