import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_cash_flow_migration_appends_us18_and_us19_without_rewriting_source_literals():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070047_cash_flow_report_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {"US-18": "Ver los saldos de cuentas de débito y efectivo.", "US-19": "Control de efectivo disponible (flujo de efectivo)."}
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "Mario Groso", "source_type": "Word", "source_reference": "source",
                "source_literal": literal, "normalized_story": "Control de cuentas y flujo",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "Mario Groso", "source_confidence": "needs_validation",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id.in_(list(literals)))
                                   .order_by(HistoryCard.story_id, HistoryCard.version)).mappings().all()
    assert {(row["story_id"], row["version"]) for row in cards} == {("US-18", 1), ("US-18", 2), ("US-19", 1), ("US-19", 2)}
    for story_id, literal in literals.items():
        versions = [row for row in cards if row["story_id"] == story_id]
        assert versions[0]["source_literal"] == versions[1]["source_literal"] == literal
        assert versions[1]["recorded_by"] == "system:implementation-iteration"


def test_transfer_migration_appends_linked_card_revisions_without_rewriting_sources():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070056_cash_transfer_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {"US-18": "Efectivo", "US-19": "Flujo", "US-35": "Relación de movimientos"}
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "Mario Groso", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": literal, "normalized_story": "Control financiero",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "Mario Groso", "source_confidence": "needs_validation",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(
            HistoryCard.story_id.in_(list(literals)), HistoryCard.iteration == migration.ITERATION,
        )).mappings().all()

    assert {row["story_id"] for row in cards} == set(literals)
    assert all(row["version"] == 2 and row["source_literal"] == literals[row["story_id"]] for row in cards)
