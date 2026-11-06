'use client';

import { useState, type FormEvent } from 'react';

export function LeadForm() {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [message, setMessage] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setState('sending'); setMessage('');
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = Object.fromEntries(form.entries());
    try {
      const response = await fetch('/api/v1/public/leads', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...payload, privacy_consent: form.get('privacy_consent') === 'on' }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No pudimos enviar tu solicitud.');
      setState('sent'); setMessage('Listo. El equipo de Arco Energy se pondrá en contacto contigo.'); formElement.reset();
    } catch (error) { setState('error'); setMessage(error instanceof Error ? error.message : 'No pudimos enviar tu solicitud.'); }
  }
  return <form className="lead-form" onSubmit={submit}>
    <label>Nombre completo<input name="name" required minLength={2} maxLength={180} autoComplete="name" placeholder="Tu nombre"/></label>
    <label>Teléfono / WhatsApp<input name="phone" required minLength={10} maxLength={40} autoComplete="tel" inputMode="tel" placeholder="10 dígitos"/></label>
    <label>Correo electrónico<input name="email" type="email" maxLength={180} autoComplete="email" placeholder="tu@correo.com"/></label>
    <label>Ciudad<input name="city" required minLength={2} maxLength={120} autoComplete="address-level2" placeholder="Tampico, Altamira…"/></label>
    <label className="lead-wide">Dirección de instalación <small>(opcional)</small><input name="address" maxLength={500} autoComplete="street-address" placeholder="Colonia o zona"/></label>
    <label className="lead-consent lead-wide"><input name="privacy_consent" type="checkbox" required/><span>Acepto que Arco Energy use estos datos para responder a mi solicitud de cotización. <a href="/privacidad">Aviso de privacidad</a></span></label>
    <label className="lead-trap" aria-hidden="true">Sitio web<input name="website" tabIndex={-1} autoComplete="off"/></label>
    <button className="primary-cta lead-wide" disabled={state === 'sending'}>{state === 'sending' ? 'Enviando…' : 'Solicitar que me contacten'} <span>↗</span></button>
    {message && <p className={`lead-message ${state}`} role={state === 'error' ? 'alert' : 'status'}>{message}</p>}
  </form>;
}
