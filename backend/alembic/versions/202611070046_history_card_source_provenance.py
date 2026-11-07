"""Add structured artifact provenance to append-only history cards.

Revision ID: 202611070046
Revises: 202611070045
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
from uuid import uuid4


revision = "202611070046"
down_revision = "202611070045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_history_cards")}
    new_columns = (
        ("source_artifact", sa.JSON()),
        ("source_language", sa.String(20)),
        ("source_attribution", sa.String(180)),
        ("source_occurred_at", sa.String(80)),
        ("source_confidence", sa.String(40)),
        ("source_links", sa.JSON()),
    )
    for name, type_ in new_columns:
        if name not in existing_columns:
            op.add_column("ae_history_cards", sa.Column(name, type_, nullable=True))

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(history)).mappings():
        updates = {}
        if not row["source_artifact"] or "artifacts" not in row["source_artifact"]:
            updates["source_artifact"] = {"artifacts": [{
                "artifact_type": row["source_type"],
                "reference": row["source_reference"] or "",
                "channel": row["source_type"],
                "location": "",
                "sha256": None,
            }]}
        if row["source_language"] is None:
            updates["source_language"] = "es"
        if not row["source_attribution"]:
            updates["source_attribution"] = row["stakeholder"]
        if row["source_confidence"] in {None, "unverified_reconstruction"}:
            updates["source_confidence"] = "needs_validation"
        if not row["source_links"]:
            updates["source_links"] = [{"artifact_index": 0, "relation": "reconstruction", "location": ""}]
        if not updates:
            continue
        bind.execute(sa.update(history).where(history.c.id == row["id"]).values(**updates))

    latest = bind.execute(sa.select(history).where(history.c.story_id == "US-42")
                          .order_by(history.c.version.desc())).mappings().first()
    if latest is not None:
        revised = dict(latest)
        revised.update({
            "id": str(uuid4()),
            "version": latest["version"] + 1,
            "iteration": "Iteración 35 · procedencia estructurada · 2026-11-07",
            "acceptance_criteria": [
                *latest["acceptance_criteria"],
                "Cada versión admite uno o más artefactos con tipo, referencia, canal, ubicación exacta y hash opcional.",
                "El relato fuente queda separado de idioma, atribución, fecha original cuando se conoce y nivel de fidelidad.",
                "Los vínculos especifican cita literal, transcripción, paráfrasis, inferencia, validación o reconstrucción.",
                "El historial previo se marca pendiente de validar cuando su fecha o confianza no está confirmada; no se inventan metadatos faltantes.",
            ],
            "unresolved_questions": [
                *latest["unresolved_questions"],
                "Los artefactos sensibles necesitan almacenamiento privado, retención y permisos; las fuentes reconstruidas deben cotejarse con cada stakeholder.",
            ],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    # Keep provenance data if application rollback is required; the prior app ignores these additive columns.
    pass
