import asyncio
from types import SimpleNamespace

from app import product_api
from app.product_api import AgentChatInput


def test_public_agent_directs_contact_to_consent_form_and_never_claims_chat_persistence(monkeypatch) -> None:
    class FakeService:
        conversation = None

        async def respond(self, *, conversation, prompt, context, model):
            self.conversation = conversation
            return SimpleNamespace(content="Respuesta de prueba")

    service = FakeService()
    monkeypatch.setattr(product_api, "_agent_service", lambda audience: service)

    result = asyncio.run(product_api._run_agent_chat(
        AgentChatInput(prompt="Quiero que me contacten"), "public", "public-session",
    ))

    system_message = next(message.content for message in service.conversation.messages if message.role == "system")
    assert result["content"] == "Respuesta de prueba"
    assert "No solicites datos personales por el chat" in system_message
    assert "formulario visible ‘Contacto comercial’" in system_message
    assert "no registra prospectos" in system_message
    assert "Si comparte datos personales aquí, no los repitas" in system_message

