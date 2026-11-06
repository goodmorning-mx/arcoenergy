import Link from 'next/link';

export const metadata = { title: 'Aviso de privacidad | Arco Energy', description: 'Información sobre el uso de los datos enviados a Arco Energy.' };

export default function PrivacyPage() {
  return <main style={{ maxWidth: 780, margin: '0 auto', padding: '48px 24px', color: '#18372a', fontFamily: 'Arial, sans-serif', lineHeight: 1.7 }}>
    <Link href="/">← Arco Energy</Link><h1>Aviso de privacidad para solicitudes de contacto</h1>
    <p>Arco Energy recibe los datos que proporcionas en el formulario de cotización para atender tu solicitud, preparar una propuesta y dar seguimiento por los medios de contacto que compartas.</p>
    <h2>Datos solicitados</h2><p>Nombre, teléfono, correo electrónico (opcional), ciudad y ubicación de instalación (opcional).</p>
    <h2>Uso y conservación</h2><p>Los datos se incorporan al registro interno de prospectos para que el equipo autorizado pueda responder. Para solicitar acceso, corrección o eliminación, escribe a <a href="mailto:hola@arcoenergy.mx">hola@arcoenergy.mx</a>.</p>
    <p>Este aviso describe el uso del formulario de contacto. La organización deberá completar sus datos legales y canales de derechos ARCO antes de habilitar publicidad indexable o campañas públicas.</p>
  </main>;
}
