import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_public_login_navigation_revision_preserves_stakeholder_literals():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070053_public_login_navigation_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {
        "US-14": "Si todo fuera desde una app, cada usuario tendrá privilegios de ver información",
        "US-39": "el CRM es el sistema de administracion es un panel dashboard para las computadoras",
        "US-40": "el PWA es una aplicacion mobile para las personas de campo y ademas un cliente para los empleados",
    }
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "owner", "source_type": "conversation", "source_reference": "source",
                "source_literal": literal, "normalized_story": "acceso por portal",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "owner", "source_confidence": "literal",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        for story_id, literal in literals.items():
            cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == story_id)
                                       .order_by(HistoryCard.version)).mappings().all()
            assert len(cards) == 2
            assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
            assert cards[1]["iteration"] == migration.ITERATION

