import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, HistoryCard, HistoryCardReview
from app.product_api import HistoryCardReviewInput, append_history_card_review
from app.roles import ROLE_PERMISSIONS
from gm_auth.models import AuthIdentity


def _identity(role="marketing"):
    return AuthIdentity(
        f"{role}-1", "arcoenergy", frozenset({role}), ROLE_PERMISSIONS[role],
        f"{role}@arcoenergy.mx", role.title(),
    )


def _review(version=1, checked=(True, False), observations=""):
    return HistoryCardReviewInput(
        story_version=version,
        checklist=[
            {"criterion": "La ruta muestra el detalle de la historia", "checked": checked[0]},
            {"criterion": "Las observaciones quedan guardadas", "checked": checked[1]},
        ],
        observations=observations,
    )


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(HistoryCard(
            story_id="US-42", version=1, iteration="Discovery", stakeholder="Stakeholders",
            source_literal="Relato original", source_type="conversation", source_reference="history-cards.md",
            normalized_story="Revisar las tarjetas en equipo",
            acceptance_criteria=["La ruta muestra el detalle de la historia", "Las observaciones quedan guardadas"],
            recorded_by="source-import",
        ))
        db.commit()
    return engine


def test_marketing_can_append_checklist_and_observation_snapshots_without_overwriting():
    engine = _database()
    with Session(engine) as db:
        first = append_history_card_review("US-42", _review(observations="Validado con marketing"), _identity(), db)
        second = append_history_card_review("US-42", _review(checked=(True, True), observations="También validado por contador"), _identity("contador"), db)
        rows = db.scalars(select(HistoryCardReview).order_by(HistoryCardReview.review_version)).all()

    assert first["review_version"] == 1
    assert second["review_version"] == 2
    assert second["reviewed_by"] == "contador@arcoenergy.mx"
    assert rows[0].observations == "Validado con marketing"
    assert rows[0].checklist[1]["checked"] is False
    assert rows[1].observations == "También validado por contador"
    assert rows[1].checklist[1]["checked"] is True
    assert rows[0].history_card_id == rows[1].history_card_id


def test_review_rejects_stale_story_version_mismatched_checklist_and_empty_submission():
    engine = _database()
    with Session(engine) as db:
        with pytest.raises(HTTPException) as stale:
            append_history_card_review("US-42", _review(version=2, observations="Nota"), _identity(), db)
        assert stale.value.status_code == 409

        mismatch = HistoryCardReviewInput(story_version=1, checklist=[{"criterion": "Otro criterio", "checked": True}])
        with pytest.raises(HTTPException) as wrong_checklist:
            append_history_card_review("US-42", mismatch, _identity(), db)
        assert wrong_checklist.value.status_code == 422

        with pytest.raises(HTTPException) as empty:
            append_history_card_review("US-42", _review(checked=(False, False)), _identity(), db)
        assert empty.value.status_code == 422
        assert db.scalars(select(HistoryCardReview)).all() == []


def test_review_permission_is_scoped_to_administration_and_business_stakeholders():
    allowed = {"administrador", "contador", "marketing"}
    for role in allowed:
        assert "history_cards:review" in ROLE_PERMISSIONS[role]
    for role in {"instalador", "cliente"}:
        assert "history_cards:review" not in ROLE_PERMISSIONS[role]
