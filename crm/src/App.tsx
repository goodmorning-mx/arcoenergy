import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { AgentChat } from '@goodmorning/gm-agent';
import { useAuth } from '@goodmorning/gm-auth';

type View = 'inicio' | 'clientes' | 'cotizaciones' | 'seguimientos' | 'instalaciones' | 'inventario' | 'catalogo' | 'equipo';
type Customer = { id: string; name: string; phone: string; email: string; city: string; address: string; status: string; source: string; created_at?: string };
type Quote = { id: string; folio: string; customer_id: string; customer?: Customer; panel_count: number; panel_brand: string; panel_watts: number; inverter: string; payment_method: string; total: number; status: string; is_demo: boolean; installation_city: string; installation_address: string; created_at: string };
type Package = { id: string; panel_count: number; panel_brand: string; panel_watts: number; panel_unit_price: number; structure_name: string; structure_price: number; inverter_options: Array<{ name: string; price_mxn: number }>; default_inverter: string; payment_methods: string[]; enabled: boolean; is_demo: boolean; price_mxn: number; system_kw: number };
type FollowUp = { id: string; customer_id: string; due_date: string; note: string; done: boolean; customer?: Customer };
type Activity = { id: string; kind: string; note: string; created_by: string; created_at: string };
type TeamMember = { id: string; name: string; email: string; roles: string[]; permissions: string[] };
type Installation = { id: string; scheduled_at: string | null; lead_installer: string; status: string; notes: string; customer?: Customer; quote_id?: string | null };
type InventoryItem = { id: string; name: string; unit: string; quantity: number; minimum_quantity: number; unit_cost: number };
type Dashboard = { customers?: number; quotes_open?: number; quotes_amount?: number; installations_active?: number; receivables_open?: number };
type CatalogPayload = { packages: Package[]; payment_methods: string[]; catalog_note: string; demo: boolean };
type Notice = { type: 'success' | 'error' | 'info'; text: string };

const apiBase = '/api/v1';
const money = (amount: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(amount || 0);
const initials = (name: string) => name.split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
const roleLabel: Record<string, string> = { admin: 'Administrador', administrador: 'Administrador', contador: 'Contador', marketing: 'Marketing', instalador: 'Instalador', cliente: 'Cliente' };
const roleOptions = [['administrador', 'Administrador'], ['contador', 'Contador'], ['marketing', 'Marketing'], ['instalador', 'Instalador'], ['cliente', 'Cliente']] as const;

async function request<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'No se pudo completar la solicitud.');
  }
  return response.json() as Promise<T>;
}


export default function App() {
  const { identity, accessToken, logout } = useAuth();
  const [view, setView] = useState<View>('inicio');
  const [notice, setNotice] = useState<Notice | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState<Dashboard>({});
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [catalog, setCatalog] = useState<CatalogPayload | null>(null);
  const [search, setSearch] = useState('');
  const [customerOpen, setCustomerOpen] = useState(false);
  const [quoteOpen, setQuoteOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [agentOpen, setAgentOpen] = useState(false);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [teamLoading, setTeamLoading] = useState(false);
  const [teamError, setTeamError] = useState('');
  const [teamName, setTeamName] = useState('');
  const [teamEmail, setTeamEmail] = useState('');
  const [teamPassword, setTeamPassword] = useState('');
  const [teamRole, setTeamRole] = useState('marketing');
  const [teamBusy, setTeamBusy] = useState(false);
  const [printQuote, setPrintQuote] = useState<Quote | null>(null);

  const can = useCallback((permission: string) => Boolean(identity?.permissions.includes(permission)), [identity]);

  const clientAccount = identity?.roles.includes('cliente') || false;
  const allowedViews = useMemo(() => clientAccount ? [] : ([
    ...(can('customers:read') || can('quotes:read') ? ['inicio' as View] : []),
    ...(can('customers:read') ? ['clientes' as View, 'seguimientos' as View] : []),
    ...(can('quotes:read') ? ['cotizaciones' as View] : []),
    ...(can('installations:read') ? ['instalaciones' as View] : []),
    ...(can('inventory:read') ? ['inventario' as View] : []),
    ...(can('team:manage') ? ['catalogo' as View, 'equipo' as View] : []),
  ]), [can, clientAccount]);
  const title: Record<View, string> = { inicio: 'Resumen', clientes: 'Clientes', cotizaciones: 'Cotizaciones', seguimientos: 'Seguimientos', instalaciones: 'Instalaciones', inventario: 'Inventario', catalogo: 'Catálogo de paquetes', equipo: 'Equipo y accesos' };

  const announce = (text: string, type: Notice['type'] = 'success') => {
    setNotice({ text, type });
    window.setTimeout(() => setNotice(null), 4200);
  };

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      if (!accessToken) return;
      const publicCatalog = await request<CatalogPayload>('/catalog');
      setCatalog(publicCatalog);
      const tasks: Promise<void>[] = [];
      if (can('customers:read')) tasks.push(request<Customer[]>('/customers', accessToken).then(setCustomers));
      if (can('quotes:read')) tasks.push(request<Quote[]>('/quotes', accessToken).then(setQuotes));
      if (can('customers:read')) tasks.push(request<FollowUp[]>('/followups', accessToken).then(setFollowups));
      if (can('customers:read')) tasks.push(request<Dashboard>('/dashboard', accessToken).then(setDashboard));
      if (can('installations:read')) tasks.push(request<Installation[]>('/installations', accessToken).then(setInstallations));
      if (can('inventory:read')) tasks.push(request<InventoryItem[]>('/inventory', accessToken).then(setInventory));
      await Promise.all(tasks);
    } catch (error) {
      announce(error instanceof Error ? error.message : 'No se pudieron cargar los datos.', 'error');
    } finally { setLoading(false); }
  }, [accessToken, can]);

  useEffect(() => { const timer = window.setTimeout(() => setAuthResolved(true), 80); return () => window.clearTimeout(timer); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (allowedViews.length && !allowedViews.includes(view)) setView(allowedViews[0]); }, [allowedViews, view]);

  useEffect(() => {
    if (!selectedCustomer || !accessToken || !can('customers:read')) { setActivities([]); return; }
    void request<Activity[]>(`/customers/${selectedCustomer.id}/activity`, accessToken).then(setActivities).catch(error => announce(error.message, 'error'));
  }, [selectedCustomer, accessToken, can]);

  useEffect(() => {
    if (!['equipo', 'instalaciones'].includes(view) || !accessToken || !can('team:manage')) return;
    setTeamLoading(true); setTeamError('');
    void request<TeamMember[]>('/team', accessToken).then(setTeam).catch(error => setTeamError(error.message || 'No se pudo cargar el equipo.')).finally(() => setTeamLoading(false));
  }, [view, accessToken, can]);

  async function createCustomer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const data = { name: String(form.get('name') || '').trim(), phone: String(form.get('phone') || '').trim(), email: String(form.get('email') || '').trim(), city: String(form.get('city') || '').trim(), address: String(form.get('address') || '').trim() };
    if (!accessToken) return;
    try {
      await request<Customer>('/customers', accessToken, { method: 'POST', body: JSON.stringify(data) });
      setCustomerOpen(false); await refresh(); announce('Cliente guardado en tu cartera.');
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo guardar el cliente.', 'error'); }
  }

  async function addActivity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selectedCustomer) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement); const note = String(form.get('note') || '').trim();
    if (!note) return;
    if (!accessToken) return;
    try { const item = await request<Activity>(`/customers/${selectedCustomer.id}/activity`, accessToken, { method: 'POST', body: JSON.stringify({ note, kind: 'nota' }) }); setActivities(rows => [item, ...rows]); formElement.reset(); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo guardar la nota.', 'error'); }
  }

  async function scheduleFollowup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selectedCustomer) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement); const dueDate = String(form.get('due_date') || ''); const note = String(form.get('note') || '').trim();
    if (!accessToken) return;
    try { await request('/followups', accessToken, { method: 'POST', body: JSON.stringify({ customer_id: selectedCustomer.id, due_date: dueDate, note }) }); await refresh(); announce('Seguimiento programado.'); formElement.reset(); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo programar.', 'error'); }
  }

  async function completeFollowup(item: FollowUp) {
    if (!accessToken) return;
    try { await request(`/followups/${item.id}`, accessToken, { method: 'PATCH', body: JSON.stringify({ done: true }) }); await refresh(); announce('Seguimiento marcado como completado.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo actualizar.', 'error'); }
  }

  async function downloadQuote(quote: Quote) {
    if (!accessToken) return;
    try {
      const response = await fetch(`${apiBase}/quotes/${quote.id}/pdf`, { headers: { Authorization: `Bearer ${accessToken}` } });
      if (!response.ok) throw new Error('No se pudo generar el PDF.');
      const url = URL.createObjectURL(await response.blob()); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${quote.folio}.pdf`; anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo descargar el PDF.', 'error'); }
  }

  async function shareQuote(quote: Quote) {
    if (quote.is_demo) { announce('Aprueba el precio del paquete antes de compartir la propuesta.', 'error'); return; }
    const phone = quote.customer?.phone?.replace(/\D/g, '') || '';
    const message = `Hola ${quote.customer?.name || ''}, te comparto la propuesta ${quote.folio} de Arco Energy por ${money(quote.total)}. Adjunto el PDF en esta conversación.`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank', 'noopener,noreferrer');
    announce('WhatsApp abrió la conversación. Adjunta el PDF descargado antes de enviarlo.', 'info');
  }

  async function markQuoteSent(quote: Quote) {
    if (quote.is_demo) { announce('Aprueba el catálogo comercial antes de marcar una propuesta como enviada.', 'error'); return; }
    if (!accessToken) return;
    try { await request(`/quotes/${quote.id}/status`, accessToken, { method: 'PATCH', body: JSON.stringify({ status: 'sent' }) }); await refresh(); announce('Cotización marcada como enviada.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo actualizar.', 'error'); }
  }

  async function createQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const customerId = String(form.get('customer_id') || ''); const packageCount = Number(form.get('panel_count')); const selectedPackage = catalog?.packages.find(item => item.panel_count === packageCount);
    if (!selectedPackage || !customerId) { announce('Selecciona cliente y paquete.', 'error'); return; }
    const customer = customers.find(item => item.id === customerId);
    const inverter = String(form.get('inverter') || selectedPackage.default_inverter);
    const paymentMethod = String(form.get('payment_method') || selectedPackage.payment_methods[0] || 'Contado');
    const installationAddress = String(form.get('installation_address') || customer?.address || '');
    const installationCity = String(form.get('installation_city') || customer?.city || '');
    if (!accessToken) return;
    try {
      const quote = await request<Quote>('/quotes', accessToken, { method: 'POST', body: JSON.stringify({ customer_id: customerId, panel_count: packageCount, installation_address: installationAddress, installation_city: installationCity, inverter, payment_method: paymentMethod }) });
      setQuoteOpen(false); await refresh(); await downloadQuote(quote); announce(`Cotización ${quote.folio} guardada como borrador.`);
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo generar la cotización.', 'error'); }
  }

  async function savePackage(event: FormEvent<HTMLFormElement>, item: Package) {
    event.preventDefault(); if (!accessToken) return false;
    const form = new FormData(event.currentTarget); const inverterOptions = String(form.get('inverters') || '').split('\n').map(line => line.trim()).filter(Boolean).map(line => { const [name, price] = line.split('|').map(part => part.trim()); return { name, price_mxn: Number(price) }; });
    const payload = { panel_brand: String(form.get('panel_brand')), panel_watts: Number(form.get('panel_watts')), panel_unit_price: Number(form.get('panel_unit_price')), structure_name: String(form.get('structure_name')), structure_price: Number(form.get('structure_price')), inverter_options: inverterOptions, default_inverter: String(form.get('default_inverter')), payment_methods: form.getAll('payment_method').map(String), enabled: form.get('enabled') === 'on', approved_prices: form.get('approved_prices') === 'on' };
    try { await request(`/catalog/${item.panel_count}`, accessToken, { method: 'PUT', body: JSON.stringify(payload) }); await refresh(); announce(payload.approved_prices ? 'Paquete guardado y aprobado para cotizar.' : 'Paquete guardado como borrador pendiente de aprobación.'); return true; }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo guardar el paquete.', 'error'); return false; }
  }

  async function createMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    setTeamBusy(true); setTeamError('');
    try {
      const created = await request<TeamMember>('/team', accessToken, { method: 'POST', body: JSON.stringify({ name: teamName, email: teamEmail, password: teamPassword, role: teamRole }) });
      setTeam(rows => [created, ...rows]); setTeamName(''); setTeamEmail(''); setTeamPassword(''); announce(`Usuario creado como ${roleLabel[teamRole]}.`);
    } catch (error) { setTeamError(error instanceof Error ? error.message : 'No se pudo crear el usuario.'); }
    finally { setTeamBusy(false); }
  }

  async function updateMemberRole(id: string, role: string) {
    if (!accessToken) return;
    try { const updated = await request<TeamMember>(`/team/${id}`, accessToken, { method: 'PATCH', body: JSON.stringify({ role }) }); setTeam(rows => rows.map(row => row.id === id ? { ...row, roles: updated.roles, permissions: updated.permissions } : row)); announce(`Rol actualizado a ${roleLabel[role]}.`); }
    catch (error) { setTeamError(error instanceof Error ? error.message : 'No se pudo actualizar el rol.'); }
  }

  if (!authResolved) return <div className="login-screen"><section className="login-card">Cargando sesión…</section></div>;
  if (window.location.pathname.replace(/\/$/, '').endsWith('/login')) return identity ? <div className="client-redirect"><a href="/crm/">Ir al panel →</a></div> : <LoginScreen />;
  if (!identity || !accessToken) { window.location.replace('/crm/login'); return null; }
  if (clientAccount) return <div className="client-redirect"><div className="brand-mark">A</div><p>Tu portal de cliente está en la aplicación móvil.</p><a href="/app/" className="button button-primary">Abrir mi portal →</a><button className="text-button" onClick={() => void logout()}>Cerrar sesión</button></div>;

  const nav: Array<[View, string, string]> = [['inicio', '◫', 'Resumen'], ['clientes', '♙', 'Clientes'], ['cotizaciones', '▤', 'Cotizaciones'], ['seguimientos', '◷', 'Seguimientos'], ...(can('installations:read') ? [['instalaciones', '⌂', 'Instalaciones']] as Array<[View, string, string]> : []), ...(can('inventory:read') ? [['inventario', '▦', 'Inventario']] as Array<[View, string, string]> : []), ...(can('team:manage') ? [['catalogo', '⊞', 'Catálogo'], ['equipo', '♧', 'Equipo']] as Array<[View, string, string]> : [])];
  const visibleCustomers = customers.filter(item => `${item.name} ${item.city} ${item.email} ${item.phone}`.toLowerCase().includes(search.toLowerCase()));

  return <div className="crm-app">
    <aside className="crm-sidebar">
      <a className="crm-brand" href="/"><span className="brand-mark">A</span><span>arco<span>energy</span><small>GESTIÓN SOLAR</small></span></a>
      <div className="sidebar-label">ESPACIO DE TRABAJO</div>
      <nav aria-label="Navegación principal">{nav.filter(([key]) => allowedViews.includes(key)).map(([key, icon, label]) => <button key={key} className={`sidebar-link ${view === key ? 'selected' : ''}`} onClick={() => setView(key)}><span>{icon}</span>{label}{key === 'seguimientos' && followups.length > 0 && <b>{followups.length}</b>}</button>)}</nav>
      <div className="sidebar-spacer" />
      <a className="sidebar-mobile-link" href="/app/">↗ App de campo</a>
      {identity?.permissions.includes('team:manage') && <button className="sidebar-mobile-link" onClick={() => setView('equipo')}>⚙ Administración</button>}
      <div className="account-chip"><span>{initials(identity.name || identity.email || 'AE')}</span><div><b>{identity.name}</b><small>{roleLabel[identity?.roles[0] || ''] || identity.email}</small></div><button title="Cerrar sesión" onClick={async () => { await logout(); window.location.replace('/crm/login'); }}>↗</button></div>
    </aside>

    <main className="crm-main">
      <header className="crm-topbar"><div className="breadcrumbs">Arco Energy <span>/</span> {title[view]}</div><div className="topbar-right"><a href="/app/" className="mobile-app-link">App de campo ↗</a><button className="icon-button" onClick={() => void refresh()} aria-label="Actualizar datos">↻</button></div></header>
      <div className="page-content">
        <div className="page-heading"><div><div className="eyebrow">ARCO ENERGY · {new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' }).toUpperCase()}</div><h1>{view === 'inicio' ? `Hola${identity?.name ? `, ${identity.name.split(' ')[0]}` : ''}` : title[view]}</h1><p>{view === 'inicio' ? 'Tu operación comercial, clientes y propuestas en un solo lugar.' : headingDescription(view)}</p></div><div className="heading-actions">{can('customers:write') && <button className="button button-outline" onClick={() => setCustomerOpen(true)}>＋ Nuevo cliente</button>}{can('quotes:write') && <button className="button button-primary" onClick={() => setQuoteOpen(true)}>＋ Crear cotización</button>}</div></div>


        {loading && <div className="inline-loading"><span className="spinner"/> Sincronizando información…</div>}

        {view === 'inicio' && <DashboardView data={dashboard} customers={customers} quotes={quotes} followups={followups} can={can} onCustomer={setSelectedCustomer} onView={setView} onComplete={completeFollowup} />}
        {view === 'clientes' && <CustomersView customers={visibleCustomers} search={search} onSearch={setSearch} onCreate={() => setCustomerOpen(true)} canCreate={can('customers:write')} onSelect={setSelectedCustomer} />}
        {view === 'cotizaciones' && <QuotesView quotes={quotes} onCreate={() => setQuoteOpen(true)} onDownload={downloadQuote} onShare={shareQuote} onMarkSent={markQuoteSent} canWrite={can('quotes:write')} />}
        {view === 'seguimientos' && <FollowupsView items={followups} onComplete={completeFollowup} onCustomer={setSelectedCustomer} />}
        {view === 'instalaciones' && <InstallationsView items={installations} customers={customers} team={team} canWrite={can('installations:write')} token={accessToken || ''} onRefresh={refresh} announce={announce} />}
        {view === 'inventario' && <InventoryView items={inventory} canManage={can('inventory:manage')} token={accessToken || ''} onRefresh={refresh} announce={announce} />}
        {view === 'catalogo' && <CatalogView catalog={catalog} onSave={savePackage} onLogin={() => window.location.assign('/crm/login')} />}
        {view === 'equipo' && <TeamView members={team} loading={teamLoading} error={teamError} name={teamName} email={teamEmail} password={teamPassword} role={teamRole} busy={teamBusy} isDemo={false} onName={setTeamName} onEmail={setTeamEmail} onPassword={setTeamPassword} onRole={setTeamRole} onSubmit={createMember} onUpdateRole={updateMemberRole} />}

        <footer className="page-foot"><span>Arco Energy · CRM</span><span>La información se actualiza desde el espacio de trabajo de Arco Energy.</span></footer>
      </div>
    </main>

    <button className={`agent-launcher ${agentOpen ? 'open' : ''}`} onClick={() => setAgentOpen(value => !value)} aria-label={agentOpen ? 'Cerrar asistente' : 'Abrir asistente'}>{agentOpen ? '×' : '✦'}</button>
    {agentOpen && <aside className="agent-panel"><div className="agent-panel-head"><div><span className="agent-spark">✦</span><div><b>Asistente Arco</b><small>Consulta clientes y paquetes autorizados</small></div></div><button onClick={() => setAgentOpen(false)} aria-label="Cerrar asistente">×</button></div><AgentChat title="¿Qué necesitas resolver?" client={async (prompt, conversationId) => request<{ conversationId: string; content: string }>(accessToken ? '/agent/chat' : '/public/agent/chat', accessToken || undefined, { method: 'POST', body: JSON.stringify({ prompt, conversation_id: conversationId }) })} initialMessages={[{ role: 'assistant', content: 'Puedo consultar resúmenes y paquetes comerciales aprobados.' }]} /><div className="agent-safety">El asistente consulta datos autorizados. No crea ni modifica registros.</div></aside>}

    {customerOpen && <Modal title="Agregar cliente" subtitle="Guarda los datos de contacto y ubicación del prospecto." onClose={() => setCustomerOpen(false)}><form className="form-grid" onSubmit={createCustomer}><Field label="Nombre completo" name="name" required placeholder="Ej. Andrea García"/><Field label="Teléfono / WhatsApp" name="phone" placeholder="833 000 0000"/><Field label="Correo" name="email" type="email" placeholder="nombre@empresa.com"/><Field label="Ciudad" name="city" required placeholder="Tampico"/><Field label="Domicilio de instalación" name="address" className="span-two" placeholder="Calle, colonia y referencias"/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setCustomerOpen(false)}>Cancelar</button><button className="button button-primary">Guardar cliente</button></div></form></Modal>}
    {quoteOpen && <QuoteComposer packages={catalog?.packages.filter(item => item.enabled) || []} customers={customers} isDemo={false} onClose={() => setQuoteOpen(false)} onSubmit={createQuote} onNewCustomer={() => { setQuoteOpen(false); setCustomerOpen(true); }} />}
    {selectedCustomer && <CustomerDrawer customer={selectedCustomer} quotes={quotes.filter(item => item.customer_id === selectedCustomer.id)} followups={followups.filter(item => item.customer_id === selectedCustomer.id)} activities={activities} isDemo={false} canWrite={can('customers:write')} onClose={() => setSelectedCustomer(null)} onAddActivity={addActivity} onSchedule={scheduleFollowup} onDownload={downloadQuote} />}
    {notice && <div className={`toast toast-${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}>{notice.type === 'success' ? '✓' : notice.type === 'error' ? '!' : 'ⓘ'} &nbsp;{notice.text}</div>}
    {printQuote && <div className="print-layer"><div className="print-document"><header><b>arco<span>energy</span></b><span>{printQuote.folio}</span></header><h1>Propuesta de sistema solar</h1><p>Cliente: {printQuote.customer?.name || 'Cliente'}</p><p>Instalación: {printQuote.installation_address}, {printQuote.installation_city}</p><div className="print-summary"><b>{printQuote.panel_count} paneles {printQuote.panel_brand} · {printQuote.panel_watts} W</b><span>Inversor: {printQuote.inverter}</span><span>Forma de pago: {printQuote.payment_method}</span><strong>Inversión estimada: {money(printQuote.total)}</strong></div>{printQuote.is_demo && <p className="print-disclaimer">DEMOSTRACIÓN — precios ilustrativos; no enviar como propuesta comercial.</p>}<button className="button button-primary no-print" onClick={() => window.print()}>Imprimir / Guardar como PDF</button><button className="text-button no-print" onClick={() => setPrintQuote(null)}>Cerrar</button></div></div>}
  </div>;
}

function headingDescription(view: View) { return ({ inicio: '', clientes: 'Consulta prospectos, contactos y actividad comercial.', cotizaciones: 'Prepara, descarga y comparte propuestas con folio.', seguimientos: 'Da continuidad a las conversaciones y registra cada contacto.', instalaciones: 'Asigna y consulta órdenes de trabajo.', inventario: 'Administra materiales, entradas y existencias.', catalogo: 'Administra paquetes, inversores, precios y formas de pago.', equipo: 'Usuarios y privilegios para cada área.' })[view] || ''; }

function DashboardView({ data, customers, quotes, followups, can, onCustomer, onView, onComplete }: { data: Dashboard; customers: Customer[]; quotes: Quote[]; followups: FollowUp[]; can: (p: string) => boolean; onCustomer: (c: Customer) => void; onView: (v: View) => void; onComplete: (f: FollowUp) => void }) {
  const recent = [...quotes].slice(0, 4);
  return <>
    <section className="metric-grid">
      {can('customers:read') && <Metric label="PROSPECTOS Y CLIENTES" value={String(data.customers ?? customers.length)} note="Registros en tu cartera" icon="♙" tone="sage"/>}
      {can('quotes:read') && <Metric label="COTIZACIONES ABIERTAS" value={String(data.quotes_open ?? quotes.filter(item => item.status === 'draft' || item.status === 'sent').length)} note={`${money(data.quotes_amount ?? quotes.filter(item => item.status === 'draft' || item.status === 'sent').reduce((sum, item) => sum + item.total, 0))} en propuestas`} icon="▤" tone="blue"/>}
      {can('customers:read') && <Metric label="SEGUIMIENTOS PENDIENTES" value={String(followups.length)} note="Próximos y vencidos" icon="◷" tone="amber"/>}
      {can('installations:read') && <Metric label="INSTALACIONES ACTIVAS" value={String(data.installations_active ?? 0)} note="Visibles para tu rol" icon="⌂" tone="mint"/>}
      {can('receivables:read') && <Metric label="CARTERA POR COBRAR" value={money(data.receivables_open ?? 0)} note="Saldo pendiente registrado" icon="$" tone="rose"/>}
    </section>
    <section className="dashboard-grid"><div className="surface-card"><div className="section-title"><div><span className="eyebrow">ACTIVIDAD RECIENTE</span><h2>Últimas cotizaciones</h2></div><button className="text-button" onClick={() => onView('cotizaciones')}>Ver todas →</button></div>{recent.length ? <div className="recent-list">{recent.map(item => <article className="recent-row" key={item.id}><span className="avatar-soft">{initials(item.customer?.name || 'AE')}</span><div className="recent-person"><b>{item.customer?.name || 'Cliente'}</b><small>{item.folio} · {item.panel_count} paneles</small></div><span className={`status-chip status-${item.status}`}>{item.is_demo ? 'DEMO' : labelStatus(item.status)}</span><b className="recent-amount">{money(item.total)}</b></article>)}</div> : <EmptyState title="Todavía no hay cotizaciones" body="Crea una propuesta para verla aquí." action="Crear cotización" onClick={() => onView('cotizaciones')}/>}</div>
      <div className="surface-card focus-card"><div className="section-title"><div><span className="eyebrow">SIGUIENTE ACCIÓN</span><h2>Seguimientos</h2></div><button className="text-button" onClick={() => onView('seguimientos')}>Ver todos →</button></div>{followups.slice(0, 4).map(item => <div className="focus-row" key={item.id}><div className="date-tile"><b>{new Date(`${item.due_date}T12:00:00`).getDate()}</b><small>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { month: 'short' }).toUpperCase()}</small></div><div><b>{item.customer?.name || 'Cliente'}</b><small>{item.note || 'Seguimiento'}</small></div><button className="check-button" title="Completar seguimiento" onClick={() => onComplete(item)}>✓</button><button className="focus-person" title="Abrir cliente" onClick={() => item.customer && onCustomer(item.customer)}>↗</button></div>)}{!followups.length && <EmptyState title="Sin seguimientos pendientes" body="Programa el próximo contacto desde la ficha del cliente."/>}</div></section>
  </>;
}

function CustomersView({ customers, search, onSearch, canCreate, onCreate, onSelect }: { customers: Customer[]; search: string; onSearch: (s: string) => void; canCreate: boolean; onCreate: () => void; onSelect: (c: Customer) => void }) {
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">CARTERA COMERCIAL</span><h2>{customers.length} contactos</h2></div><div className="toolbar-actions"><input className="search-input" value={search} onChange={event => onSearch(event.target.value)} placeholder="Buscar por nombre, ciudad o contacto"/>{canCreate && <button className="button button-primary" onClick={onCreate}>＋ Agregar cliente</button>}</div></div>{customers.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>CLIENTE</th><th>UBICACIÓN</th><th>CONTACTO</th><th>ESTADO</th><th>ORIGEN</th><th/></tr></thead><tbody>{customers.map(item => <tr key={item.id} onClick={() => onSelect(item)}><td><span className="table-person"><i>{initials(item.name)}</i><b>{item.name}<small>{item.email || 'Sin correo registrado'}</small></b></span></td><td>{item.city || '—'}<small className="sub-cell">{item.address || 'Domicilio pendiente'}</small></td><td>{item.phone || '—'}</td><td><span className="status-chip status-draft">{labelCustomerStatus(item.status)}</span></td><td>{item.source === 'public_web' ? 'Web pública' : item.source === 'demo' ? 'Demo' : 'Equipo'}</td><td><button className="icon-button" aria-label={`Ver ${item.name}`}>→</button></td></tr>)}</tbody></table></div> : <EmptyState title="No encontramos contactos" body="Cambia la búsqueda o agrega un nuevo prospecto." action={canCreate ? 'Agregar cliente' : undefined} onClick={onCreate}/>}</section>;
}

function QuotesView({ quotes, onCreate, onDownload, onShare, onMarkSent, canWrite }: { quotes: Quote[]; onCreate: () => void; onDownload: (q: Quote) => void; onShare: (q: Quote) => void; onMarkSent: (q: Quote) => void; canWrite: boolean }) {
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">PROPUESTAS SOLARES</span><h2>{quotes.length} cotizaciones</h2></div>{canWrite && <button className="button button-primary" onClick={onCreate}>＋ Nueva cotización</button>}</div>{quotes.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>FOLIO / CLIENTE</th><th>SISTEMA</th><th>INSTALACIÓN</th><th>INVERSIÓN</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{quotes.map(item => <tr key={item.id}><td><b>{item.folio}</b><small className="sub-cell">{item.customer?.name || 'Cliente'}</small></td><td>{item.panel_count} paneles · {((item.panel_count * item.panel_watts) / 1000).toFixed(1)} kWp<small className="sub-cell">{item.inverter}</small></td><td>{item.installation_city || item.customer?.city || '—'}<small className="sub-cell">{item.installation_address || item.customer?.address || 'Domicilio pendiente'}</small></td><td><b>{money(item.total)}</b>{item.is_demo && <small className="demo-sub">Precio demo</small>}</td><td><span className={`status-chip status-${item.status}`}>{labelStatus(item.status)}</span></td><td><div className="row-actions"><button title="Descargar PDF" onClick={() => onDownload(item)}>PDF</button><button title="Abrir WhatsApp" onClick={() => onShare(item)}>WhatsApp</button>{item.status === 'draft' && canWrite && <button title="Marcar como enviada" onClick={() => onMarkSent(item)}>Marcar enviada</button>}</div></td></tr>)}</tbody></table></div> : <EmptyState title="Crea tu primera cotización" body="Elige un cliente y un paquete de paneles para generar el PDF foliado." action={canWrite ? 'Nueva cotización' : undefined} onClick={onCreate}/>}</section>;
}

function FollowupsView({ items, onComplete, onCustomer }: { items: FollowUp[]; onComplete: (f: FollowUp) => void; onCustomer: (c: Customer) => void }) {
  const today = new Date().toISOString().slice(0, 10);
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">BITÁCORA COMERCIAL</span><h2>{items.length} próximos contactos</h2></div></div>{items.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>CLIENTE</th><th>NOTA DE SEGUIMIENTO</th><th>ESTADO</th><th/></tr></thead><tbody>{items.map(item => <tr key={item.id}><td>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</td><td><button className="link-button" onClick={() => item.customer && onCustomer(item.customer)}>{item.customer?.name || 'Cliente'}</button><small className="sub-cell">{item.customer?.city}</small></td><td>{item.note || 'Retomar conversación'}</td><td><span className={`status-chip ${item.due_date <= today ? 'status-overdue' : 'status-sent'}`}>{item.due_date < today ? 'Vencido' : item.due_date === today ? 'Hoy' : 'Programado'}</span></td><td><button className="button button-small button-outline" onClick={() => onComplete(item)}>Completar</button></td></tr>)}</tbody></table></div> : <EmptyState title="No tienes seguimientos pendientes" body="Desde una ficha de cliente puedes programar una fecha y agregar una nota de bitácora."/>}</section>;
}

function InventoryView({ items, canManage, token, onRefresh, announce }: { items: InventoryItem[]; canManage: boolean; token: string; onRefresh: () => Promise<void>; announce: (message: string, type?: Notice['type']) => void }) {
  async function submit(event: FormEvent<HTMLFormElement>, path: string) {
    event.preventDefault(); const form=event.currentTarget; const data=new FormData(form);
    const payload=path.endsWith('/items') ? {name:String(data.get('name')),unit:String(data.get('unit')),minimum_quantity:Number(data.get('minimum_quantity')||0),initial_quantity:Number(data.get('initial_quantity')||0),unit_cost:Number(data.get('unit_cost')||0)} : {item_id:String(data.get('item_id')),quantity:Number(data.get('quantity')),unit_cost:Number(data.get('unit_cost')),reason:String(data.get('reason')||'entrada de almacén')};
    try { await request(path, token, {method:'POST',body:JSON.stringify(payload)}); await onRefresh(); form.reset(); announce(path.endsWith('/items')?'Artículo creado.':'Entrada de almacén registrada.'); } catch(error) { announce(error instanceof Error?error.message:'No se pudo guardar.','error'); }
  }
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">ALMACÉN</span><h2>{items.length} artículos</h2></div>{canManage&&<span className="status-chip status-approved">Control de existencias</span>}</div>{canManage&&<div className="dashboard-grid"><form className="team-form" onSubmit={event=>void submit(event,'/inventory/items')}><h3>Nuevo artículo</h3><Field label="Descripción" name="name" required placeholder="Nombre del material"/><Field label="Unidad" name="unit" required defaultValue="pieza" placeholder="pieza, metro, par"/><Field label="Existencia inicial" name="initial_quantity" type="number" min="0" step="0.01" defaultValue={0}/><Field label="Mínimo de alerta" name="minimum_quantity" type="number" min="0" step="0.01" defaultValue={0}/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" defaultValue={0}/><button className="button button-primary">Agregar artículo</button></form><form className="team-form" onSubmit={event=>void submit(event,'/inventory/receive')}><h3>Entrada de almacén</h3><label className="field"><span>Artículo</span><select name="item_id" required><option value="">Selecciona material</option>{items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Cantidad recibida" name="quantity" type="number" min="0.01" step="0.01" required/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" required/><Field label="Referencia" name="reason" placeholder="Factura, proveedor o nota"/><button className="button button-primary">Registrar entrada</button></form></div>}<div className="data-table-wrap"><table className="data-table"><thead><tr><th>ARTÍCULO</th><th>EXISTENCIA</th><th>MÍNIMO</th>{canManage&&<th>COSTO UNITARIO</th>}</tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.name}<small className="sub-cell">{item.unit}</small></td><td>{item.quantity} {item.unit}</td><td>{item.minimum_quantity}</td>{canManage&&<td>{money(item.unit_cost)}</td>}</tr>)}</tbody></table>{!items.length&&<EmptyState title="Almacén sin artículos" body="Crea el catálogo de materiales reales para empezar a registrar existencias."/>}</div></section>;
}

function InstallationsView({ items, customers, team, canWrite, token, onRefresh, announce }: { items: Installation[]; customers: Customer[]; team: TeamMember[]; canWrite: boolean; token: string; onRefresh: () => Promise<void>; announce: (message: string, type?: Notice['type']) => void }) {
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const date = String(form.get('scheduled_at') || '');
    const payload = { customer_id: String(form.get('customer_id') || ''), lead_installer: String(form.get('lead_installer') || ''), scheduled_at: date ? new Date(date).toISOString() : null, notes: String(form.get('notes') || '') };
    try { await request('/installations', token, { method: 'POST', body: JSON.stringify(payload) }); await onRefresh(); event.currentTarget.reset(); announce('Orden asignada al instalador.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo crear la orden.', 'error'); }
  }
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">COORDINACIÓN DE CAMPO</span><h2>{items.length} órdenes de trabajo</h2></div></div>{canWrite && <form className="team-form" onSubmit={create}><label className="field"><span>Cliente / proyecto</span><select name="customer_id" required><option value="">Selecciona cliente</option>{customers.map(customer=><option key={customer.id} value={customer.id}>{customer.name} · {customer.city}</option>)}</select></label><label className="field"><span>Instalador responsable</span><select name="lead_installer" required><option value="">Selecciona instalador</option>{team.filter(member=>member.roles.includes('instalador')).map(member=><option key={member.id} value={member.email}>{member.name} · {member.email}</option>)}</select></label><Field label="Fecha y hora" name="scheduled_at" type="datetime-local"/><Field label="Instrucciones" name="notes" placeholder="Alcance y detalles de la orden"/><button className="button button-primary">Asignar orden de trabajo</button></form>}{items.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROYECTO</th><th>CLIENTE</th><th>CONTACTO</th><th>INSTALADOR</th><th>FECHA</th><th>ESTADO</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.quote_id||'Proyecto'}</td><td>{item.customer?.name||'Cliente'}<small className="sub-cell">{item.customer?.city}</small></td><td>{item.customer?.phone||'—'}<small className="sub-cell">{item.customer?.email||''}</small></td><td>{item.lead_installer}</td><td>{item.scheduled_at?new Date(item.scheduled_at).toLocaleString('es-MX'):'Por programar'}</td><td>{item.status}</td></tr>)}</tbody></table></div>:<EmptyState title="Sin órdenes de trabajo" body="Las asignaciones aparecerán aquí y en la PWA del instalador."/>}</section>;
}

function CatalogView({ catalog, onSave, onLogin }: { catalog: CatalogPayload | null; onSave: (event: FormEvent<HTMLFormElement>, item: Package) => Promise<boolean>; onLogin: () => void }) {
  const [editingPackage, setEditingPackage] = useState<Package | null>(null);
  const [newCount, setNewCount] = useState(4);
  const beginNewPackage = () => { if (items.some(item => item.panel_count === newCount)) { setEditingPackage(items.find(item => item.panel_count === newCount)!); return; } setEditingPackage({ id: '', panel_count: newCount, panel_brand: '', panel_watts: 0, panel_unit_price: 0, structure_name: '', structure_price: 0, inverter_options: [], default_inverter: '', payment_methods: ['Contado'], enabled: true, is_demo: false, price_mxn: 0, system_kw: 0 }); };
  const items = catalog?.packages || [];
  return <><div className="catalog-summary"><div><span className="eyebrow">CONFIGURACIÓN COMERCIAL</span><h2>Paquetes de 4 a 20 paneles</h2><p>{catalog?.catalog_note || 'Configura el catálogo de cotización.'}</p></div><div className="toolbar-actions"><select aria-label="Cantidad de paneles del paquete" value={newCount} onChange={event => setNewCount(Number(event.target.value))}>{Array.from({length:17},(_,i)=>i+4).map(count=><option key={count} value={count}>{count} paneles</option>)}</select><button className="button button-primary" onClick={beginNewPackage}>＋ Agregar paquete</button></div></div><section className="package-grid">{items.map(item => <article className="package-card" key={item.panel_count}><div className="package-head"><span className="package-count">{item.panel_count}<small>paneles</small></span><span className={`status-chip ${item.is_demo ? 'status-overdue' : 'status-approved'}`}>{item.is_demo ? 'Demo' : 'Aprobado'}</span></div><h3>{item.panel_brand} {item.panel_watts} W</h3><p>{item.system_kw.toFixed(1)} kWp · {item.default_inverter || 'Inversor pendiente'}</p><div className="package-price">{money(item.price_mxn)}<small>{item.enabled ? 'precio de paquete' : 'desactivado'}</small></div><button className="button button-outline" onClick={() => setEditingPackage(item)}>Editar paquete</button></article>)}</section>{!items.length && <EmptyState title="No hay paquetes configurados" body="Agrega los equipos y precios vigentes aprobados por Arco Energy." action="Configurar paquete" onClick={beginNewPackage}/>}
    {editingPackage && <Modal title={`${editingPackage.panel_count} paneles`} subtitle="Edita valores y marca si están aprobados para cotizar con clientes." onClose={() => setEditingPackage(null)} wide><form className="form-grid" onSubmit={async event => { if (await onSave(event, editingPackage)) setEditingPackage(null); }}><Field label="Marca de panel" name="panel_brand" required defaultValue={editingPackage.panel_brand}/><Field label="Potencia por panel (W)" name="panel_watts" type="number" min="100" max="1000" required defaultValue={editingPackage.panel_watts}/><Field label="Precio por panel (MXN)" name="panel_unit_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.panel_unit_price}/><Field label="Nombre de estructura" name="structure_name" required defaultValue={editingPackage.structure_name}/><Field label="Precio de estructura (MXN)" name="structure_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.structure_price}/><label className="field span-two">Inversores disponibles <small>Un inversor por línea: Nombre | Precio MXN</small><textarea name="inverters" required defaultValue={editingPackage.inverter_options.map(item => `${item.name} | ${item.price_mxn}`).join('\n')}/></label><Field label="Inversor predeterminado" name="default_inverter" required defaultValue={editingPackage.default_inverter}/><div className="field"><span>Formas de pago</span><div className="check-list">{['Contado', 'Financiamiento', 'Plan 24'].map(method => <label key={method}><input type="checkbox" name="payment_method" value={method} defaultChecked={editingPackage.payment_methods.includes(method)}/>{method}</label>)}</div></div><label className="check-confirm span-two"><input type="checkbox" name="enabled" defaultChecked={editingPackage.enabled}/> Paquete disponible para nuevas cotizaciones</label><label className="approval-confirm span-two"><input type="checkbox" name="approved_prices"/> Confirmo que estos precios y equipos fueron revisados y aprobados por Arco Energy.</label><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setEditingPackage(null)}>Cancelar</button><button className="button button-primary">Guardar paquete</button></div></form></Modal>}
  </>;
}

function TeamView({ members, loading, error, name, email, password, role, busy, isDemo, onName, onEmail, onPassword, onRole, onSubmit, onUpdateRole }: { members: TeamMember[]; loading: boolean; error: string; name: string; email: string; password: string; role: string; busy: boolean; isDemo: boolean; onName: (v: string) => void; onEmail: (v: string) => void; onPassword: (v: string) => void; onRole: (v: string) => void; onSubmit: (e: FormEvent<HTMLFormElement>) => void; onUpdateRole: (id: string, role: string) => void }) {
  return <><section className="surface-card team-surface"><div className="section-title"><div><span className="eyebrow">CUENTAS Y PERMISOS</span><h2>Personas en el equipo</h2></div><span className="status-chip status-approved">5 roles</span></div><p className="muted-copy">Los permisos se validan en la API además de controlar qué se muestra en cada pantalla.</p>{!isDemo && <form className="team-form" onSubmit={onSubmit}><Field label="Nombre" value={name} onChange={onName} required placeholder="Nombre completo"/><Field label="Correo" type="email" value={email} onChange={onEmail} required placeholder="persona@arcoenergy.mx"/><Field label="Contraseña temporal" type="password" value={password} onChange={onPassword} required minLength={12} placeholder="12 caracteres mínimo"/><label className="field"><span>Rol</span><select value={role} onChange={event => onRole(event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button className="button button-primary" disabled={busy}>{busy ? 'Creando…' : '＋ Crear usuario'}</button></form>}{isDemo && <p className="demo-hint">Inicia sesión como administrador para administrar las cuentas reales.</p>}{error && <p className="error-message">{error}</p>}{loading && <p className="muted-copy">Cargando equipo…</p>}<div className="team-list">{members.map(member => <div className="team-row" key={member.id}><span className="avatar-soft">{initials(member.name)}</span><div><b>{member.name}</b><small>{member.email}</small></div><select aria-label={`Rol de ${member.name}`} value={member.roles[0] || ''} disabled={isDemo} onChange={event => onUpdateRole(member.id, event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>)}{isDemo && roleOptions.map(([id, label]) => <article className="role-mini-card" key={id}><b>{label}</b><small>{roleDescription(id)}</small></article>)}</div></section></>;
}

function roleDescription(role: string) { return ({ administrador: 'Administra usuarios, configuración y todas las áreas autorizadas.', contador: 'Consulta y registra movimientos financieros según sus permisos.', marketing: 'Gestiona clientes, seguimientos y cotizaciones.', instalador: 'Consulta trabajos y materiales de campo asignados.', cliente: 'Accede solamente a su información cuando se habilite su portal.' })[role] || ''; }

function QuoteComposer({ packages, customers, isDemo, onClose, onSubmit, onNewCustomer }: { packages: Package[]; customers: Customer[]; isDemo: boolean; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onNewCustomer: () => void }) {
  const [count, setCount] = useState(packages.find(item => item.enabled)?.panel_count || 4);
  const [customerId, setCustomerId] = useState(customers[0]?.id || '');
  const selected = packages.find(item => item.panel_count === count);
  const selectedCustomer = customers.find(item => item.id === customerId);
  const [inverter, setInverter] = useState('');
  useEffect(() => setInverter(selected?.default_inverter || ''), [selected]);
  if (!selected) return <Modal title="Catálogo pendiente" subtitle="No hay paquetes activos disponibles." onClose={onClose}><EmptyState title="Configura el catálogo" body="Un administrador debe habilitar paquetes antes de cotizar."/></Modal>;
  const price = selected.panel_unit_price * count + selected.structure_price + (selected.inverter_options.find(item => item.name === (inverter || selected.default_inverter))?.price_mxn || 0);
  return <Modal title="Nueva cotización" subtitle="Selecciona cliente, sistema y forma de pago." onClose={onClose} wide><form className="form-grid" onSubmit={onSubmit}><label className="field span-two"><span>Cliente</span><select name="customer_id" value={customerId} onChange={event => setCustomerId(event.target.value)} required><option value="">Selecciona un cliente</option>{customers.map(item => <option key={item.id} value={item.id}>{item.name} · {item.city}</option>)}</select>{!customers.length && <button type="button" className="text-button" onClick={onNewCustomer}>＋ Agregar cliente</button>}</label><label className="field"><span>Cantidad de paneles</span><select name="panel_count" value={count} onChange={event => setCount(Number(event.target.value))}>{packages.filter(item => item.enabled).map(item => <option key={item.panel_count} value={item.panel_count}>{item.panel_count} paneles · {item.system_kw.toFixed(1)} kWp</option>)}</select></label><label className="field"><span>Inversor</span><select name="inverter" value={inverter || selected.default_inverter} onChange={event => setInverter(event.target.value)}>{selected.inverter_options.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label><label className="field"><span>Marca / potencia</span><div className="readonly-field">{selected.panel_brand} · {selected.panel_watts} W</div></label><label className="field"><span>Forma de pago</span><select name="payment_method">{selected.payment_methods.map(method => <option key={method}>{method}</option>)}</select></label><Field className="span-two" label="Domicilio de instalación" name="installation_address" defaultValue={selectedCustomer?.address || ''} placeholder="Calle, colonia y referencias"/><Field label="Ciudad" name="installation_city" defaultValue={selectedCustomer?.city || ''} required placeholder="Tampico"/><div className="quote-total span-two"><div><small>INVERSIÓN ESTIMADA {selected.is_demo && <b>· DEMO</b>}</small><strong>{money(price)}</strong><span>{count} × {money(selected.panel_unit_price)} panel · {selected.structure_name} · {inverter}</span></div><span>{(count * selected.panel_watts / 1000).toFixed(2)} kWp</span></div>{selected.is_demo && <div className="inline-disclaimer span-two">Los precios son ilustrativos. El PDF indicará que es demostrativo y no debe enviarse como oferta comercial.</div>}<div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={onClose}>Cancelar</button><button className="button button-primary">{isDemo ? 'Crear vista de demostración' : 'Guardar y descargar PDF'}</button></div></form></Modal>;
}

function CustomerDrawer({ customer, quotes, followups, activities, isDemo, canWrite, onClose, onAddActivity, onSchedule, onDownload }: { customer: Customer; quotes: Quote[]; followups: FollowUp[]; activities: Activity[]; isDemo: boolean; canWrite: boolean; onClose: () => void; onAddActivity: (event: FormEvent<HTMLFormElement>) => void; onSchedule: (event: FormEvent<HTMLFormElement>) => void; onDownload: (quote: Quote) => void }) {
  const [mode, setMode] = useState<'nota' | 'seguimiento'>('nota');
  const defaultDate = new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10);
  const [followupDays, setFollowupDays] = useState('3');
  const [followupDate, setFollowupDate] = useState(defaultDate);
  function selectFollowup(value: string) { setFollowupDays(value); if (value !== 'custom') setFollowupDate(new Date(Date.now() + Number(value) * 86400000).toISOString().slice(0, 10)); }
  return <div className="drawer-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><aside className="customer-drawer"><header><div><span className="eyebrow">FICHA DE CLIENTE</span><button className="drawer-close" onClick={onClose}>×</button></div><div className="drawer-profile"><span className="profile-avatar">{initials(customer.name)}</span><div><h2>{customer.name}</h2><small>{customer.city} · {labelCustomerStatus(customer.status)}</small></div></div><div className="contact-actions"><a href={customer.phone ? `tel:${customer.phone}` : undefined} aria-disabled={!customer.phone}>☎ Llamar</a><a className="wa-action" target="_blank" rel="noreferrer" href={customer.phone ? `https://wa.me/${customer.phone.replace(/\D/g, '')}` : undefined}>◉ WhatsApp</a></div><div className="contact-block"><b>Datos de contacto</b><span>{customer.phone || 'Teléfono pendiente'}</span><span>{customer.email || 'Correo pendiente'}</span><span>{customer.address || customer.city || 'Ubicación pendiente'}</span></div></header><div className="drawer-body"><section><div className="section-title"><div><span className="eyebrow">PROPUESTAS</span><h3>{quotes.length} cotizaciones</h3></div></div>{quotes.length ? quotes.map(item => <div className="drawer-quote" key={item.id}><div><b>{item.folio}</b><small>{item.panel_count} paneles · {item.status}</small></div><strong>{money(item.total)}</strong><button className="icon-button" onClick={() => onDownload(item)}>PDF</button></div>) : <p className="empty-inline">Sin cotizaciones todavía.</p>}</section><section><div className="section-title"><div><span className="eyebrow">PRÓXIMO CONTACTO</span><h3>{followups.length} seguimientos</h3></div></div>{followups.map(item => <div className="drawer-followup" key={item.id}><b>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}</b><span>{item.note}</span></div>)}</section>{canWrite && <section className="note-box"><div className="note-tabs"><button className={mode === 'nota' ? 'active' : ''} onClick={() => setMode('nota')}>Agregar nota</button><button className={mode === 'seguimiento' ? 'active' : ''} onClick={() => setMode('seguimiento')}>Programar seguimiento</button></div>{mode === 'nota' ? <form onSubmit={onAddActivity}><textarea name="note" required maxLength={5000} placeholder="Escribe una nota para la bitácora…"/><button className="button button-primary">Guardar nota</button></form> : <form onSubmit={onSchedule}><label className="field"><span>Cuándo volver a contactar</span><select value={followupDays} onChange={event => selectFollowup(event.target.value)}><option value="3">En 3 días</option><option value="7">En 7 días</option><option value="15">En 15 días</option><option value="30">En 30 días</option><option value="custom">Elegir fecha</option></select></label><label className="field"><span>Fecha para contactar</span><input name="due_date" type="date" min={new Date().toISOString().slice(0, 10)} value={followupDate} onChange={event => { setFollowupDate(event.target.value); setFollowupDays("custom"); }} required/></label><label className="field"><span>Motivo / comentario del cliente</span><textarea name="note" required placeholder="¿Qué comentó y qué hay que retomar?"/></label><button className="button button-primary">Programar contacto</button></form>}</section>}<section><div className="section-title"><div><span className="eyebrow">BITÁCORA</span><h3>Actividad reciente</h3></div></div>{activities.length ? activities.map(item => <div className="activity-row" key={item.id}><i/><div><b>{item.kind}</b><p>{item.note}</p><small>{item.created_by || 'Equipo'} · {new Date(item.created_at).toLocaleString('es-MX')}</small></div></div>) : <p className="empty-inline">Aún no hay actividad registrada.</p>}</section></div><footer className="drawer-foot">{`Origen: ${customer.source === 'public_web' ? 'Web pública' : 'Equipo Arco Energy'}`}</footer></aside></div>;
}

function Metric({ label, value, note, icon, tone }: { label: string; value: string; note: string; icon: string; tone: string }) { return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className={`metric-icon tone-${tone}`}>{icon}</i></div><strong>{value}</strong><small>{note}</small></article>; }
function EmptyState({ title, body, action, onClick }: { title: string; body: string; action?: string; onClick?: () => void }) { return <div className="empty-state"><span>✦</span><h3>{title}</h3><p>{body}</p>{action && onClick && <button className="button button-outline" onClick={onClick}>{action}</button>}</div>; }
function Modal({ title, subtitle, onClose, wide = false, children }: { title: string; subtitle: string; onClose: () => void; wide?: boolean; children: ReactNode }) { return <div className="modal-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className={`modal-card ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><header className="modal-header"><div><span className="eyebrow">ARCO ENERGY</span><h2>{title}</h2><p>{subtitle}</p></div><button className="drawer-close" onClick={onClose} aria-label="Cerrar">×</button></header><div className="modal-body">{children}</div></section></div>; }
function Field({ label, name, type = 'text', required = false, placeholder, defaultValue, value, onChange, className = '', min, max, step, minLength }: { label: string; name?: string; type?: string; required?: boolean; placeholder?: string; defaultValue?: string | number; value?: string; onChange?: (value: string) => void; className?: string; min?: string | number; max?: string | number; step?: string | number; minLength?: number }) { return <label className={`field ${className}`}><span>{label}</span><input name={name} type={type} required={required} placeholder={placeholder} defaultValue={value === undefined ? defaultValue : undefined} value={value} onChange={event => onChange?.(event.target.value)} min={min} max={max} step={step} minLength={minLength}/></label>; }
function labelStatus(status: string) { return ({ draft: 'Borrador', sent: 'Enviada', accepted: 'Aceptada', declined: 'No aceptada', overdue: 'Vencido' })[status] || status; }
function labelCustomerStatus(status: string) { return ({ lead: 'Prospecto', qualified: 'En conversación', followup: 'Seguimiento', customer: 'Cliente' })[status] || status; }
function LoginScreen() { const { login, loading, error } = useAuth(); const [failure, setFailure] = useState(''); return <div className="login-screen"><a className="crm-brand" href="/"><span className="brand-mark">A</span><span>arco<span>energy</span><small>GESTIÓN SOLAR</small></span></a><section className="login-card"><span className="eyebrow">ACCESO DE EQUIPO</span><h1>Iniciar sesión</h1><p>Ingresa con la cuenta de tu negocio.</p><form onSubmit={async event => { event.preventDefault(); const form = new FormData(event.currentTarget); setFailure(''); try { await login(String(form.get('email')), String(form.get('password')), true); window.location.replace('/crm/'); } catch (err) { setFailure(err instanceof Error ? err.message : error || 'No se pudo iniciar sesión.'); } }}><Field label="Correo electrónico" name="email" type="email" required/><Field label="Contraseña" name="password" type="password" required/><label className="field"><span><input type="checkbox" name="remember" defaultChecked/> Mantener sesión iniciada</span></label>{failure && <p role="alert">{failure}</p>}<button className="button button-primary" disabled={loading}>{loading ? 'Iniciando…' : 'Entrar'}</button></form><a href="/app/login">Acceso móvil</a></section></div>; }
