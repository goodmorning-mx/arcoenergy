import { useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@goodmorning/gm-auth';
import { PwaStatus } from '@goodmorning/gm-pwa';
import { cacheInstallations, cacheInventory, cacheMovements, checklistQueueKey, clearCachedFieldSnapshots, queueChecklistChange, queueFieldAction, readCachedInstallations, readCachedInventory, readCachedMovements, readChecklistQueue, readFieldActionQueue, removeChecklistChange, removeChecklistChangeIfCurrent, removeFieldAction, type ChecklistQueueItem, type FieldActionQueueItem, type Installation } from './offlineChecklist';
import './styles.css';
import './barcode.css';
import './offline.css';

type Screen = 'inicio' | 'cotizar' | 'instalaciones' | 'inventario' | 'cuenta';
type StockItem = { id:string; name:string; barcode?:string|null; unit:string; quantity:number; reserved_quantity?:number; available_quantity?:number; minimum_quantity:number; unit_cost:number };
type StockMovement = { id:string; item_id:string; item_name:string; quantity:number; signed_quantity:number; movement_type:string; installation_id:string|null; reason:string; related_movement_id:string|null; returnable_quantity:number };
type QuotePackage = { panel_count:number; panel_brand:string; panel_watts:number; panel_unit_price:number; structure_name:string; structure_price:number; inverter_options:Array<{name:string;price_mxn:number}>; default_inverter:string; payment_methods:string[]; enabled:boolean; pricing_approved:boolean };
type PortalData = { customers:Array<{id:string;name:string;city:string;status:string}>; quotes:Array<{id:string;folio:string;panel_count:number;panel_brand:string;panel_watts:number;inverter:string;total:number;status:string;created_at:string}>; installations:Array<{id:string;folio?:string|null;scheduled_at:string|null;status:string;checklist:Array<{task:string;done:boolean}>}>; payments:Array<{installment_number:number;due_date:string;amount:number;paid_amount:number;balance:number;status:string;payment_method:string}> };
const money = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 2 }).format(n);

function App() {
  const [screen, setScreen] = useState<Screen>('inicio');
  const [panels, setPanels] = useState(8);
  const [saved, setSaved] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerCity, setCustomerCity] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [folio, setFolio] = useState('');
  const [quoteNotice, setQuoteNotice] = useState('');
  const [liveStock, setLiveStock] = useState<StockItem[]|null>(null);
  const [liveMovements, setLiveMovements] = useState<StockMovement[]>([]);
  const [quotePackages, setQuotePackages] = useState<QuotePackage[]>([]);
  const [liveInstallations, setLiveInstallations] = useState<Installation[]|null>(null);
  const [paymentMethod, setPaymentMethod] = useState('Contado');
  const [inverter, setInverter] = useState('');
  const { identity, accessToken, logout, login, loading: authLoading, error: authError } = useAuth();
  const [loginError, setLoginError] = useState('');
  const [workInstallId, setWorkInstallId] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [notificationMessage, setNotificationMessage] = useState('');
  const [checklistBusy, setChecklistBusy] = useState('');
  const [offlineQueue, setOfflineQueue] = useState<ChecklistQueueItem[]>([]);
  const [actionQueue, setActionQueue] = useState<FieldActionQueueItem[]>([]);
  const [isOnline, setIsOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine);
  const [syncAttempt, setSyncAttempt] = useState(0);
  const syncingChecklist = useRef(false);
  const seenInstallationIds = useRef<Set<string> | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const can = (permission:string) => Boolean(identity?.permissions.includes(permission));
  const allowedScreens:Screen[] = [ ...(can('customers:read') || can('quotes:read') || can('installations:read') ? ['inicio' as Screen] : []), ...(can('quotes:write') ? ['cotizar' as Screen] : []), ...(can('installations:read') ? ['instalaciones' as Screen] : []), ...(can('inventory:read') ? ['inventario' as Screen] : []), 'cuenta' ];
  const navItems:[Screen,string,string][] = ([['inicio','⌂','Resumen'],['cotizar','＋','Cotizador'],['instalaciones','⌁','Instalaciones'],['inventario','▦','Inventario'],['cuenta','◉','Mi cuenta']] as [Screen,string,string][]).filter(([id])=>allowedScreens.includes(id));
  const selectedPackage = quotePackages.find(item => item.panel_count === panels && item.enabled);
  const selectedInverter = selectedPackage?.inverter_options.find(item => item.name === (inverter || selectedPackage.default_inverter));
  const quote = useMemo(() => ({ watts: panels * (selectedPackage?.panel_watts || 0), price: selectedPackage ? panels * Number(selectedPackage.panel_unit_price) + Number(selectedPackage.structure_price) + Number(selectedInverter?.price_mxn || 0) : 0 }), [panels, selectedPackage, selectedInverter]);

  useEffect(() => { const timer=window.setTimeout(()=>setAuthResolved(true),0); return ()=>window.clearTimeout(timer); }, []);
  useEffect(() => {
    const update = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update); };
  }, []);
  useEffect(() => {
    if (!identity?.email) { setOfflineQueue([]); return; }
    void readChecklistQueue(identity.email).then(setOfflineQueue).catch(() => setNotificationMessage('No se pudo leer la cola local de cambios.'));
    void readFieldActionQueue(identity.email).then(setActionQueue).catch(() => setActionMessage('No se pudo leer la cola local de operaciones.'));
  }, [identity?.email]);
  useEffect(() => {
    if (!accessToken || !identity?.permissions.includes('quotes:read')) { setQuotePackages([]); return; }
    void fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/catalog`).then(async response => { if (!response.ok) throw new Error('No se pudo cargar el catálogo.'); const result=await response.json(); setQuotePackages(result.packages || []); }).catch(error => setQuoteNotice(error instanceof Error ? error.message : 'No se pudo cargar el catálogo.'));
  }, [accessToken, identity?.permissions.join(',')]);
  useEffect(() => {
    if (!accessToken || !identity?.permissions.includes('installations:read')) { setLiveInstallations(null); return; }
    const loadInstallations = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/installations`, { headers: { Authorization: `Bearer ${accessToken}` } });
        if (!response.ok) throw new Error('No se pudieron cargar las instalaciones.');
        const rows: Installation[] = await response.json();
        setLiveInstallations(rows);
        if (identity?.email && identity.roles.includes('instalador')) await cacheInstallations(identity.email, rows);
      } catch {
        if (identity?.email && identity.roles.includes('instalador')) {
          const cached = await readCachedInstallations(identity.email).catch(() => null);
          if (cached) setLiveInstallations(cached);
        }
      }
    };
    void loadInstallations();
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') void loadInstallations(); }, 30000);
    return () => window.clearInterval(timer);
  }, [accessToken, identity?.permissions.join(','), identity?.email]);
  useEffect(() => {
    if (!isOnline || !accessToken || !identity?.email || syncingChecklist.current) return;
    const ownerEmail = identity.email;
    syncingChecklist.current = true;
    void (async () => {
      let needsAnotherPass = false;
      try {
        const queued = await readChecklistQueue(ownerEmail);
        if (!queued.length) { setOfflineQueue([]); return; }
        const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/installations`, { headers: { Authorization: `Bearer ${accessToken}` } });
        if (!response.ok) throw new Error('No se pudieron validar las órdenes asignadas.');
        let rows: Installation[] = await response.json();
        if (identity.roles.includes('instalador')) await cacheInstallations(ownerEmail, rows);
        for (const change of queued) {
          const installation = rows.find(row => row.id === change.installation_id);
          if (!installation) continue;
          const current = installation.checklist || [];
          const checklist = current.map(item => ({ ...item, done: item.task === change.task ? change.done : item.done }));
          if (!current.some(item => item.task === change.task)) {
            await removeChecklistChange(change.key);
            setNotificationMessage('Se descartó un cambio local porque coordinación retiró ese paso de la orden.');
            continue;
          }
          const saved = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/installations/${installation.id}/checklist`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
            body: JSON.stringify({ checklist }),
          });
          if (!saved.ok) {
            setNotificationMessage(saved.status >= 500
              ? 'El servidor no pudo sincronizar los cambios. Puedes reintentar cuando vuelva a responder.'
              : 'Un cambio local requiere revisión porque la orden o el acceso cambió. Contacta a coordinación.');
            break;
          }
          const updated: Installation = await saved.json();
          rows = rows.map(row => row.id === updated.id ? updated : row);
          const removed = await removeChecklistChangeIfCurrent(change.key, change.done);
          if (!removed) needsAnotherPass = true;
        }
        setLiveInstallations(rows);
        if (identity.roles.includes('instalador')) await cacheInstallations(ownerEmail, rows);
        const remaining = await readChecklistQueue(ownerEmail);
        setOfflineQueue(remaining);
        if (!remaining.length) setNotificationMessage('Cambios del checklist sincronizados.');
        else if (needsAnotherPass) setSyncAttempt(value => value + 1);
      } catch {
        // Keep queued edits until the server confirms them.
      } finally {
        syncingChecklist.current = false;
      }
    })();
  }, [isOnline, accessToken, identity?.email, identity?.roles.join(','), offlineQueue.length, syncAttempt]);
  useEffect(() => {
    if (!isOnline || !accessToken || !identity?.email || actionQueue.length === 0) return;
    let cancelled = false;
    void (async () => {
      const queued = await readFieldActionQueue(identity.email!);
      let applied = false;
      for (const action of queued) {
        if (cancelled) return;
        try {
          const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}${action.path}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
            body: JSON.stringify({ ...action.payload, operation_id: action.operation_id }),
          });
          if (!response.ok) {
            setActionMessage(response.status >= 500
              ? 'El servidor no confirmó una operación pendiente. Se conserva para reintentar.'
              : `Una operación pendiente requiere revisión (${response.status}). Se conserva sin aplicar cambios nuevos.`);
            break;
          }
          await removeFieldAction(action.operation_id);
          applied = true;
          setActionMessage(`${action.summary} sincronizado y confirmado por el servidor.`);
        } catch {
          setActionMessage('Sin conexión con el servidor. Las operaciones siguen guardadas en este dispositivo.');
          break;
        }
      }
      if (applied && !cancelled) {
        const headers = { Authorization: `Bearer ${accessToken}` };
        const [stockResponse, movementsResponse, installationsResponse] = await Promise.all([
          fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/inventory`, { headers }),
          fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/inventory/movements`, { headers }),
          fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/installations`, { headers }),
        ]);
        if (stockResponse.ok) { const rows: StockItem[] = await stockResponse.json(); setLiveStock(rows); await cacheInventory(identity.email!, rows); }
        if (movementsResponse.ok) { const rows: StockMovement[] = await movementsResponse.json(); setLiveMovements(rows); await cacheMovements(identity.email!, rows); }
        if (installationsResponse.ok) { const rows: Installation[] = await installationsResponse.json(); setLiveInstallations(rows); await cacheInstallations(identity.email!, rows); }
      }
      if (!cancelled) setActionQueue(await readFieldActionQueue(identity.email!));
    })();
    return () => { cancelled = true; };
  }, [isOnline, accessToken, identity?.email, actionQueue.length, syncAttempt]);
  useEffect(() => {
    if (!liveInstallations) { seenInstallationIds.current = null; return; }
    const current = new Set(liveInstallations.map(item => item.id));
    const previous = seenInstallationIds.current;
    seenInstallationIds.current = current;
    if (!previous || !identity?.roles.includes('instalador') || typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    const newlyAssigned = liveInstallations.filter(item => !previous.has(item.id));
    if (newlyAssigned.length) void navigator.serviceWorker.ready.then(async registration => {
      for (const item of newlyAssigned) await registration.showNotification(`Nueva orden ${item.folio || ''}`.trim(), {
        body: `${item.customer?.name || 'Cliente'} · ${item.customer?.city || 'Ubicación pendiente'}`,
        tag: `arcoenergy-order-${item.id}`,
        data: { url: '/app/' },
      });
    }).catch(() => setNotificationMessage('No se pudo mostrar el aviso en este dispositivo.'));
  }, [liveInstallations, identity?.roles.join(',')]);
  useEffect(() => { if (selectedPackage) { setInverter(selectedPackage.default_inverter); setPaymentMethod(selectedPackage.payment_methods[0] || 'Contado'); } }, [panels, quotePackages.length]);

  useEffect(() => { if (!allowedScreens.includes(screen)) setScreen(allowedScreens[0]); }, [identity?.roles.join(','), screen]);

  useEffect(() => {
    if (!accessToken || !identity?.permissions.includes('inventory:read')) { setLiveStock(null); return; }
    void fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/inventory`, { headers: { Authorization: `Bearer ${accessToken}` } })
      .then(async response => { if (!response.ok) throw new Error('No se pudo consultar el inventario.'); const rows: StockItem[] = await response.json(); setLiveStock(rows); if (identity?.email && identity.roles.includes('instalador')) await cacheInventory(identity.email, rows); })
      .catch(async error => { if (identity?.email && identity.roles.includes('instalador')) { const cached = await readCachedInventory<StockItem>(identity.email).catch(() => null); if (cached) { setLiveStock(cached); return; } } setQuoteNotice(error instanceof Error ? error.message : 'Error de conexión.'); });
    void fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/inventory/movements`, { headers: { Authorization: `Bearer ${accessToken}` } })
      .then(async response => { if (!response.ok) throw new Error('No se pudo cargar el historial de materiales.'); const rows: StockMovement[] = await response.json(); setLiveMovements(rows); if (identity?.email && identity.roles.includes('instalador')) await cacheMovements(identity.email, rows); })
      .catch(async error => { if (identity?.email && identity.roles.includes('instalador')) { const cached = await readCachedMovements<StockMovement>(identity.email).catch(() => null); if (cached) { setLiveMovements(cached); return; } } setQuoteNotice(error instanceof Error ? error.message : 'Error de conexión.'); });
  }, [accessToken, identity?.permissions.join(','), identity?.email]);

  if (!authResolved) return <div className="login-page"><p>Cargando sesión…</p></div>;
  if (['/login', '/app/login'].includes(window.location.pathname.replace(/\/$/, ''))) { if (identity) { window.location.replace('/app/'); return null; } return <div className="login-page"><section className="login-sheet"><div className="eyebrow">ARCOENERGY · CAMPO</div><h1>Iniciar sesión</h1><p>Acceso para personal y clientes autorizados.</p><form onSubmit={async event => {event.preventDefault(); const form=new FormData(event.currentTarget); setLoginError(''); try {await login(String(form.get('email')),String(form.get('password')),true); window.location.replace('/app/');} catch(err) {setLoginError(err instanceof Error?err.message:authError||'No se pudo iniciar sesión.');}}}><label>Correo electrónico<input name="email" type="email" autoComplete="username" required /></label><label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>{loginError&&<p role="alert">{loginError}</p>}<button className="button dark full" disabled={authLoading}>{authLoading?'Iniciando…':'Entrar'}</button></form><a href="/crm/login">Acceso de administración</a></section></div>; }
  if (!identity || !accessToken) { window.location.replace('/app/login'); return null; }
  if (identity?.roles.includes('cliente')) return <ClientPortal accessToken={accessToken||''} onLogout={()=>void logoutFieldUser()}/>;

  const selectedWorkOrder = (liveInstallations || []).find(item => item.id === workInstallId);
  const selectableStock: Array<StockItem & { orderRemaining: number }> = selectedWorkOrder?.materials
    ? selectedWorkOrder.materials.filter(line => line.remaining_quantity > 0).map(line => {
      const item = liveStock?.find(stock => stock.id === line.item_id);
      return item ? { ...item, orderRemaining: line.remaining_quantity } : null;
    }).filter((item): item is StockItem & { orderRemaining: number } => Boolean(item))
    : (liveStock || []).map(item => ({ ...item, orderRemaining: item.available_quantity ?? item.quantity }));



  async function submitFieldAction(event: React.FormEvent<HTMLFormElement>, kind: 'consume'|'return'|'expense') {
    event.preventDefault(); if (!accessToken || !identity?.email) return;
    const formElement = event.currentTarget;
    const ownerEmail = identity.email;
    const form=new FormData(event.currentTarget);
    const path=kind==='consume'?'/v1/inventory/consume':kind==='return'?'/v1/inventory/returns':'/v1/expenses';
    const payload: FieldActionQueueItem['payload']=kind==='consume'?{item_id:String(form.get('item_id')),quantity:Number(form.get('quantity')),installation_id:String(form.get('installation_id')),reason:String(form.get('reason')||'Consumo de instalación')}:kind==='return'?{out_movement_id:String(form.get('out_movement_id')),quantity:Number(form.get('quantity')),condition:String(form.get('condition')||'usable'),reason:String(form.get('reason')|| (form.get('condition')==='damaged'?'Merma de material dañado':'Devolución de material sobrante'))}:{installation_id:String(form.get('installation_id')),category:String(form.get('category')||'Viáticos'),description:String(form.get('description')||''),amount:Number(form.get('amount'))};
    const operationId=globalThis.crypto?.randomUUID?.() || `field-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const summary=kind==='consume'?'Consumo de material':kind==='return'?'Devolución/merma':'Gasto de campo';
    const queued: FieldActionQueueItem={operation_id:operationId,owner:ownerEmail,kind,path,payload,summary,queued_at:new Date().toISOString()};
    const queueLocally=async()=>{await queueFieldAction(queued);setActionQueue(await readFieldActionQueue(ownerEmail));setActionMessage(`${summary} guardado en este dispositivo. Pendiente de sincronizar.`);formElement.reset();};
    if (!isOnline || actionQueue.length>0) { try { await queueLocally(); } catch { setActionMessage('No se pudo guardar la operación localmente. Mantén esta pantalla abierta e intenta de nuevo.'); } return; }
    try {
      const response=await fetch(`${import.meta.env.VITE_API_URL||'/api'}${path}`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${accessToken}`},body:JSON.stringify({...payload,operation_id:operationId})});
      if(!response.ok){if(response.status>=500){await queueLocally();return;}throw new Error((await response.json()).detail||'No se pudo guardar el movimiento.');}
      setActionMessage(kind==='consume'?'Consumo registrado en la orden de trabajo.':kind==='return'?(String(form.get('condition')||'usable')==='damaged'?'Merma registrada y ligada al costo de la orden.':'Devolución reutilizable registrada en almacén.'):'Gasto registrado en el proyecto.');
      if(kind!=='expense'){const [stock,movements]=await Promise.all([fetch(`${import.meta.env.VITE_API_URL||'/api'}/v1/inventory`,{headers:{Authorization:`Bearer ${accessToken}`}}),fetch(`${import.meta.env.VITE_API_URL||'/api'}/v1/inventory/movements`,{headers:{Authorization:`Bearer ${accessToken}`}})]);if(stock.ok){const rows=await stock.json();setLiveStock(rows);await cacheInventory(identity.email,rows);}if(movements.ok){const rows=await movements.json();setLiveMovements(rows);await cacheMovements(identity.email,rows);}const orders=await fetch(`${import.meta.env.VITE_API_URL||'/api'}/v1/installations`,{headers:{Authorization:`Bearer ${accessToken}`}});if(orders.ok)setLiveInstallations(await orders.json());}
      formElement.reset();
    }catch(error){
      if (error instanceof TypeError || !navigator.onLine) { try { await queueLocally(); } catch { setActionMessage('Falló la conexión y no se pudo guardar la operación localmente.'); } return; }
      setActionMessage(error instanceof Error?error.message:'No se pudo guardar.');
    }
  }

  async function toggleChecklist(installation: Installation, task: string, done: boolean) {
    if (!accessToken || checklistBusy) return;
    setChecklistBusy(installation.id);
    const checklist = (installation.checklist || []).map(item => ({ ...item, done: item.task === task ? done : item.done }));
    const queuedChange: ChecklistQueueItem = {
      key: checklistQueueKey(identity?.email || '', installation.id, task),
      owner: identity?.email || '', installation_id: installation.id, task, done, queued_at: new Date().toISOString(),
    };
    const queueLocally = async () => {
      if (!identity?.email) throw new Error('No se puede asociar el cambio a la cuenta activa.');
      await queueChecklistChange(queuedChange);
      setOfflineQueue(await readChecklistQueue(identity.email));
      const updated = { ...installation, checklist };
      setLiveInstallations(rows => (rows || []).map(row => row.id === updated.id ? updated : row));
      const cachedRows = liveInstallations || [installation];
      await cacheInstallations(identity.email, cachedRows.map(row => row.id === updated.id ? updated : row));
      setNotificationMessage('Sin conexión: cambio guardado en este dispositivo y pendiente de sincronizar.');
    };
    try {
      if (!navigator.onLine || offlineQueue.length > 0) {
        await queueLocally();
        if (navigator.onLine && offlineQueue.length > 0) setSyncAttempt(value => value + 1);
        return;
      }
      let response: Response;
      try {
        response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/installations/${installation.id}/checklist`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
          body: JSON.stringify({ checklist }),
        });
      } catch { await queueLocally(); return; }
      if (!response.ok) throw new Error((await response.json()).detail || 'No se pudo actualizar la orden.');
      const updated = await response.json();
      setLiveInstallations(rows => (rows || []).map(row => row.id === updated.id ? updated : row));
      setNotificationMessage('Avance de la orden guardado.');
    } catch (error) {
      setNotificationMessage(error instanceof Error ? error.message : 'No se pudo guardar el avance.');
    } finally { setChecklistBusy(''); }
  }

  async function enableNotifications() {
    if (typeof Notification === 'undefined') { setNotificationMessage('Este navegador no admite notificaciones.'); return; }
    const permission = await Notification.requestPermission();
    setNotificationMessage(permission === 'granted' ? 'Avisos activados mientras la app esté abierta.' : 'El navegador no autorizó los avisos.');
  }

  async function logoutFieldUser() {
    let cacheCleanupFailed = false;
    if (identity?.email) {
      try { await clearCachedFieldSnapshots(identity.email); }
      catch { cacheCleanupFailed = true; }
    }
    await logout();
    if (cacheCleanupFailed) window.alert('La sesión se cerró, pero este dispositivo no confirmó la limpieza de datos guardados localmente. Cierra el navegador y solicita apoyo al administrador.');
    window.location.replace('/app/login');
  }

  async function discardPendingChecklist() {
    if (!identity?.email || !window.confirm('¿Descartar todos los cambios de checklist pendientes en este dispositivo?')) return;
    const pending = await readChecklistQueue(identity.email);
    await Promise.all(pending.map(item => removeChecklistChange(item.key)));
    setOfflineQueue([]);
    setNotificationMessage('Se descartaron los cambios locales pendientes.');
  }

  async function discardPendingActions() {
    if (!identity?.email || !window.confirm('¿Descartar todas las operaciones de campo pendientes en este dispositivo?')) return;
    const pending = await readFieldActionQueue(identity.email);
    await Promise.all(pending.map(item => removeFieldAction(item.operation_id)));
    setActionQueue([]);
    setActionMessage('Se descartaron las operaciones locales pendientes.');
  }

  async function generateQuote() {
    if (accessToken && !customerName.trim()) { setQuoteNotice('Escribe el nombre del cliente para guardar la cotización.'); return; }
    if (accessToken && customerName.trim()) {
      try {
        const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` };
        if (!selectedPackage) { setQuoteNotice('No existe un paquete activo para esta cantidad de paneles.'); return; }
        const customerResponse = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/customers`, { method: 'POST', headers, body: JSON.stringify({ name: customerName, city: customerCity, phone: customerPhone, email: customerEmail }) });
        if (!customerResponse.ok) throw new Error((await customerResponse.json()).detail || 'No se pudo guardar el cliente.');
        const customer = await customerResponse.json();
        const quoteResponse = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/quotes`, { method: 'POST', headers, body: JSON.stringify({ customer_id: customer.id, panel_count: panels, installation_city: customerCity, inverter: inverter || selectedPackage.default_inverter, payment_method: paymentMethod }) });
        if (!quoteResponse.ok) throw new Error((await quoteResponse.json()).detail || 'No se pudo crear la cotización.');
        const savedQuote = await quoteResponse.json(); setFolio(savedQuote.folio);
        const pdfResponse = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/v1/quotes/${savedQuote.id}/pdf`, { headers: { Authorization: `Bearer ${accessToken}` } });
        if (!pdfResponse.ok) throw new Error('La cotización se guardó, pero no se pudo generar su PDF.');
        const link = document.createElement('a'); link.href = URL.createObjectURL(await pdfResponse.blob()); link.download = `${savedQuote.folio}.pdf`; link.click(); URL.revokeObjectURL(link.href);
        const driveStatus = pdfResponse.headers.get('X-Drive-Status');
        setQuoteNotice(driveStatus === 'saved' ? 'PDF descargado y archivado en Drive.' : driveStatus === 'upload-failed' ? 'PDF descargado. No se pudo archivar en Drive; avisa a administración.' : 'PDF descargado. Drive aún no está configurado; el archivo no quedó archivado.');
      } catch (error) { setQuoteNotice(error instanceof Error ? error.message : 'No se pudo guardar.'); return; }
    } else { return; }
    setSaved(true);
    if (!accessToken) window.setTimeout(() => window.print(), 250);
  }

  return <div className="app-frame">
    <header className="topbar"><a className="brand" href="/"><span className="brand-mark">A</span><span>arco<span>energy</span></span></a><div className="top-actions"><PwaStatus/><button className="avatar" title="Cerrar sesión" onClick={()=>void logoutFieldUser()}>{identity.name?.slice(0,2).toUpperCase()||'AE'}</button></div></header>
    <div className="workspace"><aside className="rail"><div className="rail-label">CAMPO</div>{navItems.map(([id,icon,label])=><button key={id} className={screen===id?'rail-item active':'rail-item'} onClick={()=>setScreen(id)}><span>{icon}</span>{label}</button>)}<div className="rail-bottom"><span className="mini-avatar">{identity.name?.slice(0,2).toUpperCase()||'AE'}</span><div><b>{identity.name}</b><small>{identity.roles[0]||'Equipo'} · ArcoEnergy</small></div></div></aside>
    <main className="content">
      {screen==='inicio'&&<><div className="welcome"><div><div className="eyebrow">{new Date().toLocaleDateString('es-MX',{weekday:'long',day:'numeric',month:'long'}).toUpperCase()}</div><h1>Hola, {identity?.name?.split(' ')[0]||'equipo'} <span>☀</span></h1><p>Tu operación solar, en un solo lugar.</p></div>{can('quotes:write')&&<button className="button dark" onClick={()=>setScreen('cotizar')}>＋ Crear cotización</button>}</div><section className="stats">{can('quotes:read')&&<article><small>COTIZACIONES</small><strong>CRM</strong><span className="muted">Consulta la cartera comercial</span></article>}{can('installations:read')&&<article><small>INSTALACIONES</small><strong>Agenda</strong><span className="muted">Tareas asignadas a tu equipo</span></article>}{can('inventory:read')&&<article><small>INVENTARIO</small><strong>{liveStock?.length ?? '—'}</strong><span className="muted">Artículos disponibles</span></article>}</section><section className="overview-grid"><article className="panel pipeline"><div className="panel-head"><div><small>ACCESOS RÁPIDOS</small><h2>Tu espacio de trabajo</h2></div></div><div className="todo-row"><span className="todo-icon green">▤</span><div><b>CRM de escritorio</b><small>Clientes, cotizaciones y seguimientos</small></div><a className="arrow" href="/crm/login">↗</a></div><div className="todo-row"><span className="todo-icon blue">▦</span><div><b>Materiales del equipo</b><small>Consulta existencias autorizadas desde esta app</small></div><button className="arrow" onClick={()=>setScreen('inventario')}>↗</button></div></article><article className="panel todo"><div className="panel-head"><div><small>PARA EMPEZAR</small><h2>Acciones disponibles</h2></div></div><div className="todo-row"><span className="todo-icon amber">＋</span><div><b>Cotiza desde el celular</b><small>Usa los paquetes vigentes configurados por administración</small></div><button className="arrow" onClick={()=>setScreen('cotizar')}>↗</button></div></article></section></>}
      {screen==='cotizar'&&<><div className="page-title"><div><div className="eyebrow">VENTAS / NUEVA PROPUESTA</div><h1>Cotizador solar</h1><p>Arma una propuesta con el catálogo vigente de tu empresa.</p></div><span className="catalog-status">{!selectedPackage?'SIN PAQUETE ACTIVO':!selectedPackage.pricing_approved?'PRECIO PENDIENTE':'CATÁLOGO APROBADO'}</span></div><div className="quote-layout"><section className="panel form-panel"><h2>Cuéntanos del proyecto</h2><label>Nombre del cliente<input value={customerName} onChange={e=>setCustomerName(e.target.value)} placeholder="Ej. Andrea Martínez"/></label><label>Teléfono / WhatsApp<input value={customerPhone} onChange={e=>setCustomerPhone(e.target.value)} placeholder="833 123 4567" inputMode="tel"/></label><label>Correo del cliente<input type="email" value={customerEmail} onChange={e=>setCustomerEmail(e.target.value)} placeholder="cliente@correo.com"/></label><label>Lugar de instalación<input value={customerCity} onChange={e=>setCustomerCity(e.target.value)} placeholder="Ciudad o código postal"/></label><div className="form-row"><label>Paneles <div className="stepper"><button type="button" onClick={()=>{setSaved(false);setPanels(Math.max(4,panels-1))}}>−</button><strong>{panels}</strong><button type="button" onClick={()=>{setSaved(false);setPanels(Math.min(20,panels+1))}}>＋</button><span>paneles</span></div></label><label>Forma de pago<select value={paymentMethod} onChange={e=>setPaymentMethod(e.target.value)}>{(selectedPackage?.payment_methods||[]).map(method=><option key={method}>{method}</option>)}</select></label></div><label>Inversor recomendado<select value={inverter||selectedPackage?.default_inverter||''} onChange={e=>setInverter(e.target.value)}>{(selectedPackage?.inverter_options||[]).map(option=><option key={option.name}>{option.name}</option>)}</select></label><button className="button dark full" onClick={()=>void generateQuote()} disabled={!selectedPackage||!selectedPackage.pricing_approved||!accessToken}>{saved?'✓ Propuesta guardada':!selectedPackage?.pricing_approved?'Paquete pendiente de aprobación':'Generar propuesta y PDF'}</button>{quoteNotice&&<small className="form-error">{quoteNotice}</small>}<small className="form-note">{accessToken?'La cotización se guardará en el CRM y el PDF se descargará.':'Inicia sesión con permisos comerciales para consultar el catálogo y guardar cotizaciones.'}</small></section><section className="quote-preview"><div className="preview-top"><span>PROPUESTA</span><span>{folio}</span></div><div className="sun-art">☼</div><div className="quote-copy"><small>SISTEMA SOLAR RESIDENCIAL</small><h2>Tu energía,<br/>a tu manera.</h2><p>Un sistema diseñado para aprovechar el sol y reducir tu recibo.</p></div><div className="quote-spec"><span><b>{panels} ×</b> paneles {selectedPackage?.panel_brand||''} de {selectedPackage?.panel_watts||'—'} W</span><span><b>{(quote.watts/1000).toFixed(2)} kWp</b> capacidad · {inverter||selectedPackage?.default_inverter||'Inversor por definir'}</span></div><div className="quote-price"><small>INVERSIÓN ESTIMADA</small><strong>{!selectedPackage?.pricing_approved?'Precio por aprobar':selectedPackage?money(quote.price):'Configura el paquete'}</strong><small>{paymentMethod} · {selectedPackage?.structure_name||''}</small></div>{saved&&customerPhone&&selectedPackage&&selectedPackage.pricing_approved&&<a className="button lime full share-button" href={`https://wa.me/${customerPhone.replace(/\D/g,'')}?text=${encodeURIComponent(`Hola ${customerName||''}, te comparto tu propuesta solar ${folio}. Estoy al pendiente de tus dudas.`)}`} target="_blank" rel="noreferrer">Abrir WhatsApp · Adjunta el PDF ↗</a>}<p className="fine">Cotización sujeta a validación técnica y condiciones comerciales.</p></section></div></>}
      {screen==='instalaciones'&&<><div className="page-title"><div><div className="eyebrow">OPERACIÓN / CAMPO</div><h1>Instalaciones</h1><p>Tu agenda de trabajo y el estado de cada proyecto.</p></div>{identity?.roles.includes('instalador')&&<button className="button outline" onClick={()=>void enableNotifications()}>Activar avisos</button>}</div>{(!isOnline||offlineQueue.length>0||actionQueue.length>0)&&<div className="offline-banner" role="status"><b>{isOnline?'Cambios pendientes de sincronizar':'Sin conexión'}</b><span>{isOnline?'Los cambios locales se enviarán y confirmarán al recuperar conexión.':'Las órdenes, el inventario y las operaciones disponibles se conservan en este dispositivo para el trabajo de campo.'}</span>{(offlineQueue.length+actionQueue.length)>0&&<><small>{offlineQueue.length} checklist · {actionQueue.length} operaciones de campo pendientes</small>{isOnline&&<button className="button outline" onClick={()=>setSyncAttempt(value=>value+1)}>Reintentar sincronización</button>}{offlineQueue.length>0&&<button className="button outline" onClick={()=>void discardPendingChecklist()}>Descartar checklist</button>}{actionQueue.length>0&&<button className="button outline" onClick={()=>void discardPendingActions()}>Descartar operaciones</button>}</>}</div>}{notificationMessage&&<p className="action-message" role="status">{notificationMessage}</p>}<div className="install-list">{(liveInstallations||[]).length ? liveInstallations!.map(item=><article className="panel install-card" key={item.id}><div className="install-date">{item.scheduled_at?new Date(item.scheduled_at).toLocaleString('es-MX'):'Fecha por confirmar'}</div><div className="install-person"><span className="person-avatar">{(item.customer?.name||'AE').slice(0,2).toUpperCase()}</span><div><h2>{item.customer?.name||'Cliente'}</h2><small>{item.customer?.city||'Ubicación pendiente'}</small></div></div><div className="install-system"><b>{item.folio||item.status}</b><small>{item.notes||'Orden de trabajo'}</small></div><span className="pill scheduled">{item.checklist?.filter(task=>task.done).length||0}/{item.checklist?.length||0} pasos</span>{item.materials?.length ? <div className="order-materials"><b>Materiales para esta orden</b>{item.materials.map(line=>{const stock=liveStock?.find(row=>row.id===line.item_id);const physical=Number(stock?.quantity||0);const reserved=Number(stock?.reserved_quantity||0);const gap=Math.max(0,reserved-physical);return <div className="order-material" key={line.item_id}><span><strong>{line.item_name}</strong><small>{line.requested_quantity} solicitados · {line.consumed_quantity} usados · {line.remaining_quantity} pendientes</small></span><span className={stock?(gap>0?'stock-gap':'stock-ok'):'stock-unknown'}>{stock?gap>0?`Revisar faltante global: ${gap} ${stock.unit}`:`Reservas cubiertas · ${physical} ${stock.unit} físicos`:'Sin registro de inventario'}</span></div>})}</div>:null}{Boolean(item.checklist?.length)&&<div className="install-checklist">{item.checklist!.map(task=><label key={task.task}><input type="checkbox" checked={task.done} disabled={checklistBusy===item.id} onChange={event=>void toggleChecklist(item,task.task,event.target.checked)}/><span>{task.task}</span></label>)}</div>}{identity?.roles.includes('instalador')&&item.assigned_installers?.some(email=>email.toLowerCase()===identity.email?.toLowerCase())&&<button className="button outline" disabled={item.confirmed_installers?.some(email=>email.toLowerCase()===identity.email?.toLowerCase())||!isOnline} onClick={async()=>{try{const response=await fetch(`${import.meta.env.VITE_API_URL||'/api'}/v1/installations/${item.id}/confirm`,{method:'POST',headers:{Authorization:`Bearer ${accessToken}`}});if(!response.ok)throw new Error('No se pudo confirmar la asignación.');const confirmation=await response.json();setLiveInstallations(rows=>rows?.map(row=>row.id===item.id?{...row,confirmed_installers:[...new Set([...(row.confirmed_installers||[]),confirmation.installer_email])]}:row)||null);setNotificationMessage('Asignación confirmada y registrada.');}catch(error){setNotificationMessage(error instanceof Error?error.message:'No se pudo confirmar la asignación.');}}}>{item.confirmed_installers?.some(email=>email.toLowerCase()===identity.email?.toLowerCase())?'Asignación confirmada':'Confirmar asignación'}</button>}<button className="button outline" onClick={()=>{setWorkInstallId(item.id);setScreen('inventario')}}>Registrar material/gasto</button></article>):<section className="panel empty-state"><h2>{isOnline?'Sin instalaciones asignadas':'No hay órdenes guardadas en este dispositivo'}</h2><p>{isOnline?'Cuando coordinación te asigne una orden, aparecerá aquí.':'Conéctate una vez para cargar las órdenes asignadas antes de trabajar sin conexión.'}</p></section>}</div></>}
      {screen==='inventario'&&<><div className="page-title"><div><div className="eyebrow">OPERACIÓN / ALMACÉN</div><h1>Inventario</h1><p>Consulta existencias. Registra consumos y viáticos vinculados a una orden de trabajo.</p></div><span className="catalog-status">{liveStock?`${liveStock.length} ARTÍCULOS`:'Cargando inventario'}</span></div><BarcodeScanner items={liveStock||[]} onMatch={item=>{setActionMessage(`Artículo identificado: ${item.name} · ${item.available_quantity??item.quantity} ${item.unit} disponibles.`);document.getElementById(`stock-${item.id}`)?.scrollIntoView({behavior:'smooth',block:'center'});}}/><section className="stats">{(can('inventory:costs:read')||can('inventory:manage'))&&<article><small>VALOR ESTIMADO</small><strong>{liveStock?money(liveStock.reduce((sum,item)=>sum+item.quantity*item.unit_cost,0)):'—'}</strong><span className="muted">{liveStock?'Costo registrado':'Cargando inventario'}</span></article>}<article><small>STOCK BAJO</small><strong>{liveStock?liveStock.filter(item=>item.minimum_quantity>0&&(item.available_quantity??item.quantity)<=item.minimum_quantity).length:'—'}</strong><span className="warn">Requieren revisión</span></article><article><small>ASIGNADO A PROYECTOS</small><strong>{liveStock?'Consultar instalación':'—'}</strong><span className="muted">Material para cuadrillas</span></article></section><section className="panel inventory-list"><div className="table-head inv-head"><span>ARTÍCULO</span><span>DISPONIBLE</span><span>ASIGNADO</span><span>ESTADO</span></div>{liveStock?.length ? liveStock.map((item,i)=><div className="inv-row" id={`stock-${item.id}`} key={item.id}><span className="item-cell"><i>{['▧','⌁','▤','⌁','⟐'][i%5]}</i><b>{item.name}<small>{item.barcode||'Sin código registrado'}</small></b></span><b>{item.available_quantity ?? item.quantity} {item.unit}</b><span>{item.reserved_quantity ?? 0} {item.unit}</span><em className={`pill ${item.minimum_quantity>0&&(item.available_quantity??item.quantity)<=item.minimum_quantity?'scheduled':'sent'}`}>{item.minimum_quantity>0&&(item.available_quantity??item.quantity)<=item.minimum_quantity?'Disponibilidad baja':'Disponible'}</em></div>):<div className="empty-state"><h3>Inventario sin artículos</h3><p>El catálogo se mostrará cuando administración registre artículos y existencias.</p></div>}</section>{(identity.permissions.includes('inventory:write')||identity.permissions.includes('expenses:write'))&&<section className="panel field-actions"><h2>Registrar movimiento de campo</h2><label>Orden de trabajo<select value={workInstallId} onChange={e=>setWorkInstallId(e.target.value)} required><option value="">Selecciona una instalación</option>{(liveInstallations||[]).map(item=><option key={item.id} value={item.id}>{item.folio||'Orden'} · {item.customer?.name||'Cliente'} · {item.customer?.city||item.status}</option>)}</select></label>{identity.permissions.includes('inventory:write')&&<form onSubmit={e=>void submitFieldAction(e,'consume')}><h3>Material utilizado</h3><select name="installation_id" value={workInstallId} onChange={e=>setWorkInstallId(e.target.value)} required><option value="">Orden de trabajo</option>{(liveInstallations||[]).map(item=><option key={item.id} value={item.id}>{item.customer?.name||'Cliente'}</option>)}</select><select name="item_id" required><option value="">Artículo</option>{selectableStock.map(item=><option key={item.id} value={item.id}>{item.name} · pendiente en esta orden {item.orderRemaining} {item.unit}</option>)}</select><input name="quantity" type="number" min="0.01" step="0.01" placeholder="Cantidad utilizada" required/><input name="reason" placeholder="Nota del consumo"/><button className="button dark">Descontar material</button></form>}{identity.permissions.includes('inventory:write')&&<form onSubmit={e=>void submitFieldAction(e,'return')}><h3>Devolver sobrantes</h3><select name="out_movement_id" required><option value="">Salida de material de esta orden</option>{liveMovements.filter(movement=>movement.movement_type==='out'&&movement.installation_id===workInstallId&&movement.returnable_quantity>0).map(movement=><option key={movement.id} value={movement.id}>{movement.item_name} · quedan {movement.returnable_quantity}</option>)}</select><input name="quantity" type="number" min="0.01" step="0.01" placeholder="Cantidad" required/><select name="condition"><option value="usable">Sobrante reutilizable: regresa a almacén</option><option value="damaged">Pieza dañada: registrar merma</option></select><input name="reason" placeholder="Estado o nota del material"/><button className="button outline">Registrar devolución</button></form>}{identity.permissions.includes('expenses:write')&&<form onSubmit={e=>void submitFieldAction(e,'expense')}><h3>Viáticos y gastos</h3><input type="hidden" name="installation_id" value={workInstallId}/><select name="category"><option>Viáticos</option><option>Combustible</option><option>Materiales</option><option>Otro</option></select><input name="description" placeholder="Concepto del gasto" required/><input name="amount" type="number" min="0.01" step="0.01" placeholder="Importe MXN" required/><button className="button dark">Registrar gasto</button></form>}{actionMessage&&<p role="status">{actionMessage}</p>}</section>}</>}
      {screen==='cuenta'&&<><div className="page-title"><div><div className="eyebrow">PERFIL</div><h1>Mi cuenta</h1><p>Sesión activa del equipo ArcoEnergy.</p></div></div><section className="panel account-card"><span className="person-avatar">{(identity.name||identity.email||'AE').slice(0,2).toUpperCase()}</span><div><h2>{identity.name}</h2><p>{identity.roles[0]||'Equipo'} · arcoenergy</p><span className="pill sent">Cuenta activa</span></div><a className="button outline" href="/crm/login">Abrir CRM</a><button className="button outline" onClick={()=>void logoutFieldUser()}>Cerrar sesión</button></section><section className="panel integrations"><h2>Conexiones del negocio</h2><div><span className="integration-icon">G</span><span><b>Google Drive</b><small>El almacenamiento se conecta al configurar la cuenta del negocio.</small></span><em>Pendiente de conectar</em></div><div><span className="integration-icon">⌕</span><span><b>WhatsApp</b><small>Abre una conversación con el cliente desde el CRM.</small></span><em>Enlace disponible</em></div></section></>}
    </main></div><nav className="mobile-nav">{navItems.map(([id,icon,label])=><button key={id} className={screen===id?'selected':''} onClick={()=>setScreen(id)}><span>{icon}</span>{label==='Resumen'?'Inicio':label==='Instalaciones'?'Obras':label==='Inventario'?'Stock':label==='Mi cuenta'?'Más':label}</button>)}</nav>

  </div>
}

type BarcodeResult = { rawValue: string };
type BarcodeDetectorLike = { detect: (source: HTMLVideoElement) => Promise<BarcodeResult[]> };
type BarcodeDetectorCtor = new (options?: { formats?: string[] }) => BarcodeDetectorLike;
type BarcodeDetectorApi = { BarcodeDetector?: BarcodeDetectorCtor; getSupportedFormats?: () => Promise<string[]> };

function BarcodeScanner({ items, onMatch }: { items: StockItem[]; onMatch: (item: StockItem) => void }) {
  const [code, setCode] = useState('');
  const [scanning, setScanning] = useState(false);
  const [notice, setNotice] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const normalized = (value: string) => value.trim().toLocaleLowerCase();

  useEffect(() => {
    if (!scanning) return;
    let active = true;
    let stream: MediaStream | undefined;
    let frame = 0;
    const start = async () => {
      const api = window as Window & BarcodeDetectorApi;
      if (!api.BarcodeDetector || !navigator.mediaDevices?.getUserMedia) {
        setNotice('Este navegador no permite leer códigos con la cámara. Captura o escanea el código en el campo para identificar el artículo.');
        setScanning(false);
        return;
      }
      try {
        const supported = api.getSupportedFormats ? await api.getSupportedFormats() : [];
        const requested = ['qr_code', 'ean_13', 'ean_8', 'code_128', 'upc_a', 'upc_e', 'itf', 'data_matrix'];
        const formats = supported.length ? requested.filter(format => supported.includes(format)) : [];
        const detector = new api.BarcodeDetector(formats.length ? { formats } : undefined);
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
        if (!active || !videoRef.current) { stream.getTracks().forEach(track => track.stop()); return; }
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        const detect = async () => {
          if (!active || !videoRef.current) return;
          try {
            const [result] = await detector.detect(videoRef.current);
            if (result?.rawValue) {
              setCode(result.rawValue);
              identify(result.rawValue);
              return;
            }
          } catch { /* Keep the camera active while a frame is not decodable. */ }
          frame = window.requestAnimationFrame(() => void detect());
        };
        frame = window.requestAnimationFrame(() => void detect());
      } catch {
        setNotice('No se pudo iniciar la cámara. Revisa el permiso del navegador o captura el código manualmente.');
        setScanning(false);
      }
    };
    void start();
    return () => {
      active = false;
      window.cancelAnimationFrame(frame);
      stream?.getTracks().forEach(track => track.stop());
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [scanning]);

  function identify(value: string) {
    const item = items.find(row => (row.barcode && normalized(row.barcode) === normalized(value)) || normalized(`AE-${row.id}`) === normalized(value));
    if (!item) { setNotice(`El código ${value} no está asignado a un artículo del catálogo.`); return; }
    setNotice(`Artículo identificado: ${item.name}`);
    setScanning(false);
    onMatch(item);
  }

  return <section className="panel barcode-lookup">
    <div><small>IDENTIFICAR MATERIAL</small><h2>Escanea el código del artículo</h2><p>Usa la cámara o un lector que escriba el código en el campo.</p></div>
    <form onSubmit={event => { event.preventDefault(); setNotice(''); identify(code); }}>
      <input aria-label="Código QR o de barras" value={code} onChange={event => setCode(event.target.value)} placeholder="Escanea o escribe el código" autoComplete="off" />
      <button className="button dark" type="submit" disabled={!code.trim()}>Buscar</button>
      <button className="button outline" type="button" onClick={() => { setNotice(''); setScanning(value => !value); }}>{scanning ? 'Cerrar cámara' : 'Abrir cámara'}</button>
    </form>
    {scanning && <video className="barcode-camera" ref={videoRef} muted playsInline aria-label="Vista de cámara para escanear el artículo" />}
    {notice && <p className="barcode-notice" role="status">{notice}</p>}
  </section>;
}

function ClientPortal({accessToken,onLogout}:{accessToken:string;onLogout:()=>void}) {
  const [data,setData]=useState<PortalData|null>(null);
  const [error,setError]=useState('');
  useEffect(()=>{let active=true;void fetch('/api/v1/client/portal',{headers:{Authorization:`Bearer ${accessToken}`}}).then(async r=>{if(!r.ok)throw new Error((await r.json()).detail||'No pudimos cargar tu información.');return r.json();}).then(value=>{if(active)setData(value);}).catch(e=>{if(active)setError(e instanceof Error?e.message:'No pudimos cargar tu información.');});return()=>{active=false;};},[accessToken]);
  return <div className="app-frame"><header className="topbar"><a className="brand" href="/app/"><span className="brand-mark">A</span><span>arco<span>energy</span></span></a><div className="top-actions"><span>Mi cuenta</span><button className="login-small" onClick={onLogout}>Cerrar sesión</button></div></header><main className="content" style={{maxWidth:1100,margin:'0 auto',padding:'40px 24px'}}><div className="page-title"><div><div className="eyebrow">PORTAL DE CLIENTE</div><h1>Hola{data?.customers[0]?.name?`, ${data.customers[0].name.split(' ')[0]}`:''}</h1><p>Consulta tus propuestas, la instalación y tus pagos.</p></div></div>{error&&<section className="panel"><p role="alert">{error}</p></section>}{!data&&!error&&<section className="panel"><p>Cargando tu información…</p></section>}{data&&<><section className="stats"><article><small>PROPUESTAS</small><strong>{data.quotes.length}</strong></article><article><small>INSTALACIONES</small><strong>{data.installations.length}</strong></article><article><small>SALDO PENDIENTE</small><strong>{money(data.payments.reduce((sum,p)=>sum+p.balance,0))}</strong></article></section><section className="panel activity"><h2>Mis propuestas</h2>{data.quotes.length?data.quotes.map(q=><div className="table-row" key={q.id}><b>{q.folio}<small>{q.panel_count} paneles {q.panel_brand} de {q.panel_watts} W</small></b><span>{q.inverter}</span><strong>{money(q.total)}</strong><span>{q.status}</span></div>):<p>Aún no tienes propuestas registradas.</p>}</section><section className="panel activity"><h2>Mis instalaciones</h2>{data.installations.length?data.installations.map(i=><div className="table-row" key={i.id}><b>{i.folio||'Orden'} · {i.scheduled_at?new Date(i.scheduled_at).toLocaleDateString('es-MX'):'Fecha por confirmar'}</b><span>{i.status}</span><span>{i.checklist.filter(c=>c.done).length} de {i.checklist.length} pasos</span></div>):<p>Aún no tienes instalaciones programadas.</p>}</section><section className="panel activity"><h2>Mis pagos</h2>{data.payments.length?data.payments.map((p,index)=><div className="table-row" key={`${p.installment_number}-${index}`}><b>Pago {p.installment_number}<small>{new Date(`${p.due_date}T12:00:00`).toLocaleDateString('es-MX')}</small></b><span>{p.payment_method}</span><strong>{money(p.balance)}</strong><span>{p.status}</span></div>):<p>No hay pagos programados.</p>}</section></>}</main></div>;
}

export default App;
