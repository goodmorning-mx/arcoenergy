from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.agent_intents import AgentActionIntentStore, current_agent_intent_id
from app.models import AgentActionIntent, Base, Customer
from gm_mcp import Permission, RequestContext, ToolCall, ToolRegistry, tool


def _context(user_id="user-1", conversation_id="conversation-1"):
    return RequestContext(
        user_id, "arcoenergy", "arcoenergy", frozenset({"read", "write"}),
        metadata={"conversation_id": conversation_id},
    )


def _store():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as db:
        db.add(Customer(name="Rosa Martínez", city="Tampico"))
    return factory, AgentActionIntentStore(factory)


def test_confirmation_preview_is_owner_bound_and_does_not_store_raw_arguments():
    factory, store = _store()
    args = {"customer_name": "Rosa Martínez", "due_date": "2026-11-20", "note": "Llamar para revisar"}
    preview = store.preview(context=_context(), tool_name="arcoenergy.schedule_followup", arguments=args, idempotency_key=None)

    assert preview["status"] == "pending"
    assert "Rosa Martínez" in preview["details"][0]
    with factory() as db:
        row = db.get(AgentActionIntent, preview["intent_id"])
        assert row is not None
        assert row.arguments_hash != str(args)
        assert "Rosa Martínez" not in repr(row)
        assert "Llamar para revisar" not in repr(row)

    store.validate_confirmation(
        context=_context(), tool_name="arcoenergy.schedule_followup", arguments=args,
        intent_id=preview["intent_id"], confirmation_token=preview["confirmation_token"],
        idempotency_key=preview["idempotency_key"],
    )
    with pytest.raises(HTTPException) as wrong_user:
        store.validate_confirmation(
            context=_context("user-2"), tool_name="arcoenergy.schedule_followup", arguments=args,
            intent_id=preview["intent_id"], confirmation_token=preview["confirmation_token"],
            idempotency_key=preview["idempotency_key"],
        )
    assert wrong_user.value.status_code == 409
    with pytest.raises(HTTPException) as changed_args:
        store.validate_confirmation(
            context=_context(), tool_name="arcoenergy.schedule_followup", arguments={**args, "note": "otra nota"},
            intent_id=preview["intent_id"], confirmation_token=preview["confirmation_token"],
            idempotency_key=preview["idempotency_key"],
        )
    assert changed_args.value.status_code == 409


def test_intent_registry_requires_confirmation_and_replay_returns_same_result_once():
    factory, store = _store()
    registry = ToolRegistry(intent_store=store)
    executions = []

    @tool(
        name="arcoenergy.schedule_followup", description="Schedule a follow-up",
        input_schema={"type": "object"}, permission=Permission.WRITE, write=True,
        requires_confirmation=True, permissions={"write"},
    )
    def schedule(*, context, customer_name, due_date, note):
        executions.append(current_agent_intent_id())
        return {"status": "scheduled", "due_date": due_date}

    registry.register(schedule)
    args = {"customer_name": "Rosa Martínez", "due_date": "2026-11-20", "note": "Llamar"}
    context = _context()

    import asyncio
    preview = asyncio.run(registry.invoke(ToolCall("arcoenergy.schedule_followup", args), context))
    assert preview.requires_confirmation
    assert executions == []
    confirmation = preview.content
    call = ToolCall(
        "arcoenergy.schedule_followup", args, confirmed=True,
        intent_id=confirmation["intent_id"], confirmation_token=confirmation["confirmation_token"],
        idempotency_key=confirmation["idempotency_key"],
    )
    first = asyncio.run(registry.invoke(call, context))
    second = asyncio.run(registry.invoke(call, context))
    assert first.content == second.content == {"status": "scheduled", "due_date": "2026-11-20"}
    assert len(executions) == 1
    with factory() as db:
        row = db.get(AgentActionIntent, confirmation["intent_id"])
        assert row.status == "executed"
        assert row.completed_at is not None


def test_duplicate_customer_match_cannot_be_confirmed():
    factory, store = _store()
    with factory.begin() as db:
        db.add(Customer(name="Rosa Martínez", city="Altamira"))
    preview = store.preview(
        context=_context(), tool_name="arcoenergy.schedule_followup",
        arguments={"customer_name": "Rosa Martínez", "due_date": "2026-11-20", "note": "Llamar"},
        idempotency_key=None,
    )
    assert preview["status"] == "rejected"
    assert "No se creó" in preview["details"][0]
    assert not preview.get("intent_id")
