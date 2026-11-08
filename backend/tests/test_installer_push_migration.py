import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select

from app.models import HistoryCard


def test_installer_push_revision_adds_subscription_store_and_preserves_source_cards():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080073_installer_push_subscriptions.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {
        "US-7": "notificar a los instaladores que ya hay una instalación",
        "US-40": "el PWA es una aplicación mobile para las personas de campo",
    }
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1,
                "iteration": "source", "stakeholder": "Goito",
                "source_literal": literal, "source_type": "WhatsApp",
                "source_reference": "source", "normalized_story": "aviso de asignación",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "Goito", "source_confidence": "literal",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert "ae_push_subscriptions" in inspect(connection).get_table_names()
        assert {column["name"] for column in inspect(connection).get_columns("ae_push_subscriptions")} >= {
            "installer_email", "endpoint", "p256dh", "auth", "created_at",
        }
        revised_cards = {}
        for story_id, literal in literals.items():
            cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == story_id)
                                       .order_by(HistoryCard.version)).mappings().all()
            assert [row["version"] for row in cards] == [1, 2]
            assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
            assert cards[1]["iteration"] == migration.ITERATION
            revised_cards[story_id] = cards[1]

    assert any("con la PWA cerrada" in text for text in revised_cards["US-7"]["acceptance_criteria"])
    assert any("cuando la interfaz no está abierta" in text for text in revised_cards["US-40"]["acceptance_criteria"])
