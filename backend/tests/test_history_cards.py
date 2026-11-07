import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, HistoryCard
from app.product_api import HistoryCardInput, append_history_card
from gm_auth.models import AuthIdentity

ROOT = Path(__file__).resolve().parents[2]


def test_initial_history_cards_keep_literal_sources_and_all_42_ids() -> None:
    rows = json.loads((ROOT / "backend/app/history_card_initial.json").read_text(encoding="utf-8"))
    assert len(rows) == 42
    assert {row["story_id"] for row in rows} == {f"US-{number}" for number in range(1, 43)}
    assert all(row["version"] == 1 and row["source_literal"].strip() for row in rows)
    assert all(row["normalized_story"].strip() for row in rows)
    assert "firmar de manera electrónica" in rows[5]["source_literal"]
    assert "asignación de tareas" in rows[6]["source_literal"]
    assert rows[32]["source_type"] == "WhatsApp audio ASR"
    assert "sin validar" in rows[32]["source_reference"] or "contador-whatsapp-audio" in rows[32]["source_reference"]


def test_history_card_adds_new_version_without_replacing_previous() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(HistoryCard(story_id="US-1", version=1, iteration="Discovery inicial", stakeholder="Goito", source_literal="Texto original", source_type="WhatsApp", normalized_story="Story anterior", recorded_by="test"))
        db.commit()
        result = append_history_card(
            HistoryCardInput(story_id="US-1", version=2, iteration="Iteración 2", stakeholder="Goito", source_literal="Aclaración literal", source_type="WhatsApp", source_reference="private://whatsapp/story-1", normalized_story="Story actualizada"),
            AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"team:manage"}), "admin@example.test", "Admin"),
            db,
        )
        cards = db.scalars(select(HistoryCard).where(HistoryCard.story_id == "US-1").order_by(HistoryCard.version)).all()
        assert result["version"] == 2
        assert [card.source_literal for card in cards] == ["Texto original", "Aclaración literal"]
        with pytest.raises(HTTPException) as error:
            append_history_card(
                HistoryCardInput(story_id="US-1", version=2, iteration="Iteración 2", stakeholder="Goito", source_literal="No se sobrescribe", source_type="WhatsApp", source_reference="private://whatsapp/story-1", normalized_story="Story"),
                AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"team:manage"}), "admin@example.test", "Admin"),
                db,
            )
        assert error.value.status_code == 409


def test_history_card_persists_artifact_provenance_and_source_relationships():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"team:manage"}), "admin@example.test", "Admin")
    with Session(engine) as db:
        result = append_history_card(
            HistoryCardInput(
                story_id="US-42", version=1, iteration="Iteración de fuentes", stakeholder="Mario Groso",
                source_literal="Registrar siempre el mensaje literal.", source_type="WhatsApp",
                source_reference="private://whatsapp/2026-11-07", normalized_story="Preservar procedencia",
                source_artifacts=[
                    {"artifact_type": "Audio", "reference": "private://audio/1", "channel": "WhatsApp", "location": "00:12", "sha256": "a" * 64},
                    {"artifact_type": "Transcripción", "reference": "private://transcript/1", "channel": "ASR", "location": "línea 3"},
                ],
                source_links=[
                    {"artifact_index": 0, "relation": "transcription", "location": "00:12"},
                    {"artifact_index": 1, "relation": "transcription", "location": "línea 3"},
                ],
                source_language="es-MX", source_attribution="Mario Groso, transcrito por el equipo",
                source_occurred_at="2026-11-07T12:00:00-06:00", source_confidence="transcription",
            ), identity, db,
        )
        card = db.get(HistoryCard, result["id"])
        assert card is not None
        assert card.source_artifact["artifacts"][0]["sha256"] == "a" * 64
        assert card.source_links[1]["artifact_index"] == 1
        assert card.source_links[0]["relation"] == "transcription"
        assert card.source_attribution == "Mario Groso, transcrito por el equipo"
        assert card.source_occurred_at == "2026-11-07T12:00:00-06:00"
        assert card.source_confidence == "transcription"


def test_history_card_rejects_source_link_to_missing_artifact():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db, pytest.raises(HTTPException) as error:
        append_history_card(
            HistoryCardInput(
                story_id="US-42", version=1, iteration="Fuentes", stakeholder="Stakeholder",
                source_literal="Texto literal", source_type="WhatsApp", source_reference="private://source", normalized_story="Historia",
                source_artifacts=[{"artifact_type": "WhatsApp", "reference": "private://source"}],
                source_links=[{"artifact_index": 1, "relation": "literal"}],
            ),
            AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"team:manage"}), "admin@example.test", "Admin"), db,
        )
    assert error.value.status_code == 422
