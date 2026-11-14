"""Durable, single-use confirmation records for CRM agent writes."""
from __future__ import annotations

from contextvars import ContextVar
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import secrets
from uuid import uuid4

from fastapi import HTTPException
from gm_mcp import RequestContext
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.models import AgentActionIntent, Customer

_current_agent_intent: ContextVar[str | None] = ContextVar("current_agent_intent", default=None)


def current_agent_intent_id() -> str | None:
    return _current_agent_intent.get()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _arguments_hash(arguments: dict) -> str:
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return _hash(canonical)


class AgentActionIntentStore:
    """Stores only argument hashes and one-way token hashes, never CRM payloads."""

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def preview(self, *, context: RequestContext, tool_name: str, arguments: dict, idempotency_key: str | None):
        if tool_name != "arcoenergy.schedule_followup":
            raise HTTPException(403, "Esta acción no está habilitada para confirmación.")
        customer_name = str(arguments.get("customer_name", "")).strip()
        customer_city = str(arguments.get("customer_city", "")).strip()
        due_date = str(arguments.get("due_date", "")).strip()
        note = str(arguments.get("note", "")).strip()
        try:
            date.fromisoformat(due_date)
        except ValueError:
            return {"status": "rejected", "summary": "La fecha del seguimiento no es válida.", "details": ["No se creó ningún seguimiento."]}
        if not 2 <= len(customer_name) <= 180 or len(customer_city) > 120 or len(note) > 5000:
            return {"status": "rejected", "summary": "Los datos del seguimiento exceden los límites permitidos.", "details": ["No se creó ningún seguimiento."]}
        with self.session_factory() as db:
            query = select(Customer).where(func.lower(Customer.name) == customer_name.lower())
            if customer_city:
                query = query.where(func.lower(Customer.city) == customer_city.lower())
            matches = db.scalars(query.limit(2)).all()
        if len(matches) != 1:
            count = "No encontré un cliente con esos datos." if not matches else "Encontré más de un cliente con esos datos. Aclara la ciudad y vuelve a solicitarlo."
            return {
                "status": "rejected", "summary": count,
                "details": ["No se creó ni modificó ningún seguimiento."],
            }

        intent_id = str(uuid4())
        token = secrets.token_urlsafe(32)
        idem = str(uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=10)
        with self.session_factory.begin() as db:
            db.add(AgentActionIntent(
                id=intent_id, organization_id=context.organization_id, user_id=context.user_id,
                conversation_id=context.metadata.get("conversation_id", ""), tool_name=tool_name,
                arguments_hash=_arguments_hash(arguments), confirmation_token_hash=_hash(token),
                idempotency_key=idem, status="pending", expires_at=expires_at,
                created_at=now,
            ))
        return {
            "status": "pending", "intent_id": intent_id, "confirmation_token": token,
            "idempotency_key": idem, "expires_at": expires_at.isoformat(),
            "summary": "Programar seguimiento del cliente",
            "details": [
                f"Cliente: {matches[0].name}", f"Fecha: {due_date}",
                *([f"Ciudad: {matches[0].city}"] if matches[0].city else []),
                *( [f"Nota: {note}"] if note else [] ),
                "La acción se registrará en la bitácora del cliente.",
            ],
        }

    def validate_confirmation(self, *, context: RequestContext, tool_name: str, arguments: dict,
                              intent_id: str, confirmation_token: str, idempotency_key: str) -> None:
        with self.session_factory() as db:
            row = db.get(AgentActionIntent, intent_id)
        if not self._matches(row, context, tool_name, intent_id, confirmation_token):
            raise HTTPException(409, "La confirmación no coincide con una acción pendiente válida.")
        if row.arguments_hash != _arguments_hash(arguments) or row.idempotency_key != idempotency_key:
            raise HTTPException(409, "Los datos de la acción cambiaron después de la vista previa.")

    async def confirm(self, *, context: RequestContext, tool_name: str, intent_id: str | None,
                      confirmation_token: str | None, execute):
        with self.session_factory() as db:
            row = db.get(AgentActionIntent, intent_id) if intent_id else None
            if not self._matches(row, context, tool_name, intent_id or "", confirmation_token or ""):
                raise HTTPException(409, "La confirmación expiró o ya no es válida.")
            if row.status == "executed":
                return row.result or {"status": "executed"}
            if row.status == "pending":
                row.status = "executing"
                db.commit()
            elif row.status != "executing":
                raise HTTPException(409, "La acción ya no está pendiente.")

        token = _current_agent_intent.set(intent_id)
        try:
            result = execute()
            if hasattr(result, "__await__"):
                result = await result
        except Exception:
            # Keep the intent recoverable. Mutating handlers must use intent_id as
            # their unique idempotency key before a retry can execute again.
            raise
        finally:
            _current_agent_intent.reset(token)

        safe_result = json.loads(json.dumps(result, default=str))
        with self.session_factory.begin() as db:
            row = db.get(AgentActionIntent, intent_id)
            if row.status != "executed":
                row.status = "executed"
                row.result = safe_result
                row.completed_at = datetime.now(timezone.utc)
        return safe_result

    @staticmethod
    def _matches(row, context, tool_name, intent_id, token) -> bool:
        if row is None:
            return False
        now = datetime.now(timezone.utc)
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return (
            row.id == intent_id and row.user_id == context.user_id
            and row.organization_id == context.organization_id
            and row.conversation_id == context.metadata.get("conversation_id", "")
            and row.tool_name == tool_name and row.confirmation_token_hash == _hash(token)
            and row.status in {"pending", "executing", "executed"} and expires_at > now
        )
