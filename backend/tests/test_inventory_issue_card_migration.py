import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_issue_migration_preserves_source_and_grants_only_accounting_roles():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611060044_work_order_material_issue.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    from sqlalchemy import MetaData, Table, Column, String, JSON
    membership_table = Table("gm_auth_memberships", MetaData(),
        Column("user_id", String, primary_key=True), Column("organization_id", String, primary_key=True),
        Column("roles", JSON), Column("permissions", JSON))
    membership_table.create(engine)
    source_literal = "Subir orden de trabajo para registrar salida de almacén y devoluciones."
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-25", "version": 1, "iteration": "initial",
            "stakeholder": "Mario Groso", "source_type": "WhatsApp", "source_reference": "source",
            "source_literal": source_literal, "normalized_story": "Controlar salida de material",
            "acceptance_criteria": ["Registrar salida y devoluciones"], "unresolved_questions": [],
            "linked_cards": [], "recorded_by": "source-import", "created_at": now,
        })
        for user_id, role in (("a", "administrador"), ("c", "contador"), ("m", "marketing"), ("i", "instalador")):
            connection.execute(membership_table.insert(), {"user_id": user_id, "organization_id": "org",
                "roles": [role], "permissions": ["existing:permission"]})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-25")
                                   .order_by(HistoryCard.version)).mappings().all()
        grants = {row["user_id"]: set(row["permissions"]) for row in connection.execute(select(membership_table)).mappings()}

    assert [card["version"] for card in cards] == [1, 2]
    assert cards[0]["source_literal"] == cards[1]["source_literal"] == source_literal
    assert any("previsualiza localmente" in question for question in cards[1]["unresolved_questions"])
    assert "inventory:issue" in grants["a"] and "inventory:issue" in grants["c"]
    assert "inventory:issue" not in grants["m"] and "inventory:issue" not in grants["i"]
