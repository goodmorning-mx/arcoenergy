"""Record the next stakeholder iteration for collections and customer accounts.

Revision ID: 202611280164
Revises: 202611270163
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611280164"
down_revision = "202611270163"
branch_labels = None
depends_on = None

CARDS = [
    {
        "story_id": "US-57",
        "iteration": "CRM · Cobranza: tarjetas primero y calendario con vista previa",
        "stakeholder": "Stakeholder Arco Energy · autor por confirmar",
        "requested_by": "Usuario Arco Energy · autor por confirmar",
        "source_literal": "cambia el orden, cambia las tarjetas del cliente primero y despues el calendario; ademas marca con un recuadro de color el Hoy en el calendario, ademas en el calendario muestra el preview de que cliente tiene que pagar",
        "normalized_story": "Como persona de cobranza, quiero ver primero las tarjetas de clientes y después el calendario, identificar hoy de inmediato y ver en cada fecha qué clientes tienen un pago.",
        "acceptance_criteria": [
            "Las tarjetas de clientes aparecen antes del calendario en el módulo de Cobranza.",
            "El día de hoy tiene un recuadro de color claramente distinguible en el calendario.",
            "Cada fecha con vencimientos muestra una vista previa con el nombre de uno o más clientes.",
            "Cada fecha conserva un resumen del importe y número de cuotas; al seleccionarla se filtra la cartera por fecha.",
        ],
        "solution": "Se colocó la cartera por cliente antes del calendario, se resaltó Hoy con borde y fondo verde, y cada día con pagos muestra nombres de clientes más el total y número de cuotas.",
    },
    {
        "story_id": "US-58",
        "iteration": "CRM · Clientes vinculados al balance general",
        "stakeholder": "Stakeholder Arco Energy · autor por confirmar",
        "requested_by": "Usuario Arco Energy · autor por confirmar",
        "source_literal": "los clientes deben aparecer en el modulo de clientes; deben ser los mismos clientes que aparecen en el balance general, como cuenta de clientes.",
        "normalized_story": "Como administrador y contador, quiero consultar en Clientes las mismas personas vinculadas a las subcuentas de Cuentas por cobrar del balance general y ver el saldo de su subcuenta.",
        "acceptance_criteria": [
            "El directorio muestra los registros de cliente asociados a subcuentas contables de Cuentas por cobrar.",
            "La asociación usa el mismo customer_id que el balance general y no crea contactos duplicados por nombre.",
            "Cada tarjeta autorizada muestra el saldo calculado desde los cargos y abonos publicados de su subcuenta.",
            "El endpoint de saldos exige permiso accounts:read y no expone importes a roles sin acceso contable.",
            "Al abrir Clientes se actualiza el directorio y las subcuentas desde la API.",
        ],
        "solution": "Se agregó una consulta protegida por permisos que calcula el saldo desde las subcuentas contables vinculadas al cliente; el directorio prioriza a quienes tienen saldo y muestra el mismo importe del balance general.",
    },
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ae_history_cards") or not inspector.has_table("ae_history_card_reviews"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    now = datetime.now(timezone.utc)
    for row in CARDS:
        existing = bind.execute(sa.select(cards).where(cards.c.story_id == row["story_id"]).order_by(cards.c.version.desc()).limit(1)).mappings().first()
        if existing:
            card_id, version = existing["id"], existing["version"]
        else:
            card_id, version = str(uuid4()), 1
            bind.execute(cards.insert().values(
                id=card_id, version=version, source_type="conversation", source_language="es",
                source_artifact={"type": "conversation", "captured_as": "literal", "reference": "Conversación Arco Energy · Iteración de Cobranza y Clientes · 28/11/2026"},
                source_attribution=row["stakeholder"], source_confidence="direct_quote", source_links=[],
                unresolved_questions=[], linked_cards=[], recorded_by="Codex · implementación", created_at=now,
                source_reference="Conversación Arco Energy · Iteración de Cobranza y Clientes · 28/11/2026",
                acceptance_criteria=row["acceptance_criteria"],
                **{key: value for key, value in row.items() if key not in {"acceptance_criteria", "solution"}},
            ))
        reviewed = bind.execute(sa.select(reviews.c.id).where(
            reviews.c.story_id == row["story_id"], reviews.c.story_version == version,
        ).limit(1)).first()
        if reviewed:
            continue
        review_version = (bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(
            reviews.c.story_id == row["story_id"],
        )).scalar_one_or_none() or 0) + 1
        bind.execute(reviews.insert().values(
            id=str(uuid4()), story_id=row["story_id"], history_card_id=card_id,
            story_version=version, review_version=review_version,
            checklist=[{"criterion": criterion, "checked": False} for criterion in row["acceptance_criteria"]],
            observations="Pendiente de revisión funcional con los stakeholders de Cobranza, Contabilidad y Clientes.",
            finished=False, solution_proposed=row["solution"], reviewed_by="Codex · implementación", created_at=now,
        ))


def downgrade():
    # Discovery history is append-only and remains available on code rollback.
    pass
