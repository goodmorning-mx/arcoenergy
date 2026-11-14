import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import JSON, Column, MetaData, String, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

from app.models import HistoryCard


def _load_migration():
    path = Path(__file__).parents[1] / "alembic/versions/202611140154_story_card_review_workspace.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_creates_review_history_grants_only_business_roles_and_appends_us42():
    migration = _load_migration()
    engine = create_engine("sqlite://")
    metadata = MetaData()
    memberships = Table(
        "gm_auth_memberships", metadata,
        Column("user_id", String(80), primary_key=True),
        Column("organization_id", String(80), primary_key=True),
        Column("roles", JSON, nullable=False),
        Column("permissions", JSON, nullable=False),
    )
    with engine.begin() as connection:
        HistoryCard.__table__.create(connection)
        memberships.create(connection)
        now = datetime.now(timezone.utc)
        connection.execute(HistoryCard.__table__.insert().values(
            id=str(uuid4()), story_id="US-42", version=1, iteration="Discovery", stakeholder="Stakeholders",
            source_literal="Conserva literalmente cada tarjeta.", source_type="conversation", source_reference="history-cards.md",
            source_artifact={}, source_language="es", source_attribution="Equipo", source_occurred_at=None,
            source_confidence="verbatim", source_links=[], normalized_story="Conservar las tarjetas",
            acceptance_criteria=["Registrar fuentes literales"], unresolved_questions=[], linked_cards=[],
            recorded_by="source-import", created_at=now,
        ))
        for user_id, role in (("admin", "administrador"), ("accountant", "contador"), ("marketing", "marketing"), ("installer", "instalador"), ("client", "cliente")):
            connection.execute(memberships.insert().values(
                user_id=user_id, organization_id="arcoenergy", roles=[role], permissions=["existing:permission"],
            ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

    inspector = inspect(engine)
    assert inspector.has_table("ae_history_card_reviews")
    assert {column["name"] for column in inspector.get_columns("ae_history_card_reviews")} >= {
        "story_id", "history_card_id", "story_version", "review_version", "checklist", "observations", "reviewed_by", "created_at",
    }
    with engine.connect() as connection:
        rows = connection.execute(select(memberships)).mappings().all()
        grants = {row["user_id"]: migration.REVIEW_PERMISSION in row["permissions"] for row in rows}
        history = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-42").order_by(HistoryCard.version)).mappings().all()
    assert grants == {"admin": True, "accountant": True, "marketing": True, "installer": False, "client": False}
    assert len(history) == 2
    assert history[1]["source_literal"] == history[0]["source_literal"]
    assert migration.ACCEPTANCE_CRITERION in history[1]["acceptance_criteria"]
