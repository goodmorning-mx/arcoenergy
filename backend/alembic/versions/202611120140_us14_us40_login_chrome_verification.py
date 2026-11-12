"""Record Chrome verification of protected login routes for US-14 and US-40.

Revision ID: 202611120140
Revises: 202611120139
"""
from datetime import datetime, timezone
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = "202611120140"
down_revision = "202611120139"
branch_labels = None
depends_on = None
ITERATION = "Iteración 128 · verificación Chrome de login en PWA y CRM · 2026-11-12"
REVISIONS = {
    "US-14": (
        ["CI run 43245435339 pasó en Chrome las rutas `/crm/`, `/crm/login` y `/login` sin sesión, comprobando que se renderiza LoginScreen."],
        ["Queda validar privilegios y alcance por entidad/campo con cuentas reales de cada rol."],
    ),
    "US-40": (
        ["CI run 43245435339 pasó en Chrome `/app/` y `/app/login` sin sesión y comprobó el formulario de inicio de sesión."],
        ["Queda validar la experiencia autenticada en teléfonos reales de instaladores y clientes."],
    ),
}

def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({"id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc)})
        bind.execute(history.insert().values(**revised))

def downgrade() -> None:
    pass
