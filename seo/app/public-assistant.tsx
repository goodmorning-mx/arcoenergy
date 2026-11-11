'use client';

import { AgentChat } from '@goodmorning/gm-agent';

export function PublicAssistant() {
  return <div className="public-assistant"><p>Pregunta por el proceso o por los tamaños de sistema disponibles. El asistente no da precios sin aprobación del equipo. El chat no guarda solicitudes ni datos de contacto; para que te contacten, usa el formulario comercial.</p><AgentChat title="Asistente de cotización" initialMessages={[{ role: 'assistant', content: 'Hola. Puedo explicarte el proceso y consultar paquetes con precios aprobados. Si quieres que el equipo te contacte, usa el formulario comercial: el chat no guarda solicitudes ni datos personales.' }]} client={async (prompt, conversationId) => {
    const response = await fetch('/api/v1/public/agent/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt, conversation_id: conversationId }) });
    const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'El asistente no está disponible ahora. Puedes pedir que te contacten.'); return body;
  }}/></div>;
}
