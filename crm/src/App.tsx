Warning: truncated output (original token count: 57089)
Total output lines: 1403

import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react';
import { AgentChat } from '@goodmorning/gm-agent';
import { useAuth } from '@goodmorning/gm-auth';
import { QRCodeSVG } from 'qrcode.react';
import { OperationsReportView } from './OperationsReportView';
import { InventoryIssueIntake } from './InventoryIssueIntake';
import { addCalendarDaysToIsoDate, addLocalCalendarDays, localDateInputValue } from './dateUtils';
import './inventory-labels.css';
import './integrations.css';

type View = 'inicio' | 'clientes' | 'cotizaciones' | 'ventas' | 'seguimientos' | 'proyectos' | 'instalaciones' | 'inventario' | 'gastos' | 'cobranza' | 'cuentas' | 'proveedores' | 'compras' | 'reportes' | 'catalogo' | 'equipo' | 'integraciones' | 'historial';
type Customer = { id: string; name: string; phone: string; email: string; city: string; address: string; status: string; source: string; created_at?: string };
type Quote = { id: string; folio: string; customer_id: string; customer?: Customer; panel_count: number; panel_brand: string; panel_watts: number; inverter: string; payment_method: string; total: number; status: string; pricing_approved: boolean; installation_city: string; installation_address: string; created_at: string };
type Package = { id: string; panel_count: number; panel_brand: string; panel_watts: number; panel_unit_price: number; structure_name: string; structure_price: number; inverter_options: Array<{ name: string; price_mxn: number }>; default_inverter: string; payment_methods: string[]; enabled: boolean; pricing_approved: boolean; price_mxn: number; system_kw: number };
type FollowUp = { id: string; customer_id: string; due_date: string; note: string; done: boolean; assigned_to: string; customer?: Customer };
type Activity = { id: string; kind: string; note: string; created_by: string; created_at: string };
type TeamMember = { id: string; name: string; email: string; roles: string[]; permissions: string[] };
type RoleDefinition = { id: string; label: string; permissions: string[] };
type Project = { id:string; code:string; customer_id:string; name:string; notes:string; created_at:string; customer?:Customer; work_orders:Array<{id:string;folio:string|null;status:string;scheduled_at:string|null}>; status:'planning'|'active'|'completed' };
type Installation = { id: string; folio?: string | null; project_id?:string|null; project?:{id:string;code:string;name:string}|null; scheduled_at: string | null; lead_installer: string; assigned_installers?: string[]; confirmed_installers?: string[]; status: string; notes: string; customer?: Customer; quote_id?: string | null; materials?: Array<{ id: string; item_id: string; item_name: string; requested_quantity: number; preissued_quantity: number; consumed_quantity: number; remaining_quantity: number; remaining_to_issue: number; available_for_order: number | null; shortage_quantity: number }> };
type InventoryItem = { id: string; name: string; description?: string; category?: string; subcategory?:string; brand?: string; model?: string; supplier_id?: string | null; barcode?: string | null; unit: string; quantity: number; reserved_quantity?: number; available_quantity?: number; minimum_quantity: number; restock_responsible_email?: string; unit_cost: number };
type InventoryMovement = { id: string; item_id: string; item_name: string; unit: string; quantity: number; signed_quantity: number; movement_type: string; unit_cost?: number | null; reason: string; created_by: string; created_at: string; installation_id?: string | null; related_movement_id?: string | null; returnable_quantity?: number; can_reverse?: boolean };
type ProjectExpense = { id: string; installation_id: string | null; project_id?:string|null; project_code?:string; account_id: string | null; account_name: string | null; category: string; expense_type: 'fixed' | 'variable' | 'unclassified'; description: string; amount: number; receipt_url: string; receipt_available?: boolean; receipt_drive_available?: boolean; receipt_filename?: string | null; occurred_on: string; created_by: string; project_customer: string; project_city: string; reversal_of_id?: string | null; can_reverse?: boolean };
type FinancialAccount = { id: string; name: string; account_type: 'cash' | 'bank'; opening_balance: number; opening_balance_date: string; current_balance: number; movement_count: number };
type CashMovement = { id: string; account_id: string; direction: 'in' | 'out'; amount: number; category: string; description: string; occurred_on: string; source_type: string; source_id: string | null; reversal_of_id: string | null; created_by: string };
type Supplier = { id: string; name: string; rfc: string; phone: string; email: string; payment_terms: 'cash' | 'credit'; credit_days: number; active: boolean; current_balance: number };
type Purchase = { id: string; folio: string; supplier_id: string; supplier?: { id: string; name: string }; invoice_number: string; invoice_available?: boolean; invoice_filename?: string; invoice_content_type?: string; payment_terms: 'cash' | 'credit'; purchase_date: string; due_date: string | null; total: number; paid_amount: number; balance: number; status: string; can_reverse?: boolean; correction?: { reason: string } | null; payments?: Array<{ id: string; amount: number; paid_on: string; reference: string; is_reversal: boolean; can_reverse: boolean }>; lines: Array<{ id: string; item_name: string; quantity: number; unit_cost: number; line_total: number }> };
type CfdiProposal = { invoice_reference:string; purchase_date:string; supplier_rfc:string; supplier_name:string; declared_subtotal:number; global_discount:number; declared_total:number; requires_accounting_review:boolean; concepts:Array<{identifier:string;product_service_key:string;description:string;quantity:number;unit:string;net_line_amount:number;unit_cost_before_global_adjustments:number}> };
type InvoiceSuggestionField = 'supplier_rfc'|'invoice_reference'|'purchase_date'|'declared_total';
type InvoiceFieldSuggestion = { value:string; source:string };
type InvoiceTextProposal = { filename:string; extraction_method:'texto_pdf'|'ocr'; extracted_text:string; suggestions:Record<InvoiceSuggestionField,InvoiceFieldSuggestion[]>; review_only:true; source_stored:false; purchase_created:false };
type Receivable = { id: string; customer_id: string; customer?: Customer; quote_id: string | null; due_date: string; amount: number; paid_amount: number; balance: number; installment_number: number; payment_method: string; status: 'pending' | 'partial' | 'overdue' | 'paid'; payments?: Array<{ id: string; amount: number; paid_on: string; reference: string; account_name: string; is_reversal: boolean; can_reverse: boolean }> };
type Installer = { email: string; name: string };
type Sale = { id: string; folio: string; customer_id: string; customer?: Customer; quote_id: string; quote?: { id: string; folio: string; payment_method: string }; installation_id: string; installation?: Installation; sale_type: 'cash' | 'credit'; total: number; receivable?: { due_date: string; amount: number; paid_amount: number } | null; receivables?: Array<{ installment_number: number; due_date: string; amount: number }>; installment_count?: number; materials: Array<{ id: string; item_name: string; quantity: number }>; created_at: string; can_reverse?: boolean; correction?: { reason: string; created_at: string; amount: number } | null };
type Dashboard = { customers?: number; quotes_open?: number; quotes_amount?: number; quotes_pending_approval?:number; installations_active?: number; receivables_open?: number; receivables_overdue?:{count:number;amount:number}; due_receivables?: Array<{id:string;customer:string;due_date:string;balance:number;status:'due'|'overdue'}>; low_stock_items?: Array<{id:string;name:string;unit:string;available_quantity:number;minimum_quantity:number}>; inventory_summary?:{total_items:number;available_items:number;low_stock_items:number;out_of_stock_items:number}; inventory_activity_7d?:Array<{date:string;entries:number;exits:number}>; account_balances?: Array<{id:string;name:string;account_type:string;balance:number}> };
type CatalogPayload = { packages: Package[]; payment_methods: string[]; catalog_note: string };
type ProfitabilityRow = { project_id?:string|null; project_code?:string; installation_id: string | null; folio: string | null; project: string; city: string; sales: number; materials_cost: number | null; expenses: number; expenses_by_category: Record<string, number>; expenses_by_type: { fixed:number; variable:number; unclassified:number }; returns_and_bonifications:number; adjustments_by_type:{return:number;bonification:number}; preliminary_result: number | null; missing_cost_movements: number; material_events: number };
type ProfitabilityAdjustment = { id:string; installation_id:string|null; adjustment_type:'return'|'bonification'; description:string; amount:number; occurred_on:string; project:string; folio:string|null; can_reverse:boolean };
type ProfitabilityReport = { period: string; basis: string; rows: ProfitabilityRow[]; totals: { sales: number; materials_cost: number | null; expenses: number; expenses_by_type: { fixed:number; variable:number; unclassified:number }; returns_and_bonifications:number; adjustments_by_type:{return:number;bonification:number}; preliminary_result: number | null; missing_cost_movements: number }; returns_and_bonifications: { recorded: boolean; included: boolean; total:number }; complete_financial_statement: boolean };
type Notice = { type: 'success' | 'error' | 'info'; text: string };
type PendingQuoteShare = { quote: Quote; file: File; message: string; driveStatus: string };

const apiBase = '/api/v1';
const money = (amount: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 2 }).format(amount || 0);
function supportsPdfFileShare(file: File) {
  try { return typeof navigator.share === 'function' && Boolean(navigator.canShare?.({ files: [file] })); }
  catch { return false; }
}
function downloadPdfFile(file: File) {
  const url = URL.createObjectURL(file);
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = file.name; anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
const cancunDate = () => {
  const parts = new Intl.DateTimeFormat('en', { timeZone: 'America/Cancun', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
  const part = (type: string) => parts.find(item => item.type === type)?.value || '';
  return `${part('year')}-${part('month')}-${part('day')}`;
};
async function activeFieldServiceWorker() {
  const registration = await navigator.serviceWorker.register('/app/sw.js', { scope: '/app/' });
  if (registration.active) return registration;
  const worker = registration.installing || registration.waiting;
  if (!worker) throw new Error('No se pudo activar el servicio de notificaciones.');
  await new Promise<void>((resolve, reject) => {
    const finish = () => {
      if (worker.state === 'activated') resolve();
      else if (worker.state === 'redundant') reject(new Error('No se pudo activar el servicio de notificaciones.'));
    };
    worker.addEventListener('statechange', finish);
    finish();
  });
  return registration;
}
const initials = (name: string) => name.split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
const roleLabel: Record<string, string> = { admin: 'Administrador', administrador: 'Administrador', contador: 'Contador', marketing: 'Marketing', instalador: 'Instalador', cliente: 'Cliente' };
const roleOptions = [['administrador', 'Administrador'], ['contador', 'Contador'], ['marketing', 'Marketing'], ['instalador', 'Instalador'], ['cliente', 'Cliente']] as const;
const permissionLabel: Record<string, string> = {
  'customers:read': 'Consultar clientes', 'customers:write': 'Crear y actualizar clientes',
  'quotes:read': 'Consultar cotizaciones', 'quotes:write': 'Crear cotizaciones',
  'installations:read': 'Consultar instalaciones', 'installations:write': 'Administrar instalaciones',
  'inventory:read': 'Consultar inventario', 'inventory:write': 'Registrar movimientos de inventario',
  'inventory:manage': 'Administrar catálogo y costos', 'inventory:costs:read': 'Consultar costos de inventario',
  'inventory:issue': 'Emitir y devolver material de órdenes',
  'expenses:read': 'Consultar gastos', 'expenses:write': 'Registrar gastos',
  'receivables:read': 'Consultar cuentas por cobrar', 'receivables:write': 'Registrar cobranza',
  'accounts:read': 'Consultar caja y bancos', 'accounts:write': 'Registrar movimientos de cuentas',
  'accounts:manage': 'Administrar cuentas financieras', 'suppliers:read': 'Consultar proveedores',
  'suppliers:manage': 'Administrar proveedores', 'purchases:read': 'Consultar compras y CxP',
  'purchases:write': 'Registrar compras y pagos', 'sales:read': 'Consultar ventas',
  'sales:write': 'Registrar ventas', 'reports:read': 'Consultar reportes',
  'team:manage': 'Administrar usuarios y roles', 'client:portal': 'Consultar su propio portal de cliente',
};

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
  const [followupPushActive, setFollowupPushActive] = useState(false);
  const [catalog, setCatalog] = useState<CatalogPayload | null>(null);
  const [search, setSearch] = useState('');
  const [customerOpen, setCustomerOpen] = useState(false);
  const [quoteOpen, setQuoteOpen] = useState(false);
  const [pendingQuoteShare, setPendingQuoteShare] = useState<PendingQuoteShare|null>(null);
  const [quoteShareBusyId, setQuoteShareBusyId] = useState('');
  const [quoteShareError, setQuoteShareError] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [agentOpen, setAgentOpen] = useState(false);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [roleDefinitions, setRoleDefinitions] = useState<RoleDefinition[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [inventoryMovements, setInventoryMovements] = useState<InventoryMovement[]>([]);
  const [expenses, setExpenses] = useState<ProjectExpense[]>([]);
  const [pendingExpenseReceipt, setPendingExpenseReceipt] = useState<{expense:ProjectExpense;file:File}|null>(null);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [accountMovements, setAccountMovements] = useState<CashMovement[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [receivables, setReceivables] = useState<Receivable[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [installers, setInstallers] = useState<Installer[]>([]);
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
    ...(can('sales:read') ? ['ventas' as View] : []),
    ...(can('installations:read') ? ['proyectos' as View] : []),
    ...(can('installations:read') ? ['instalaciones' as View] : []),
    ...(can('inventory:read') ? ['inventario' as View] : []),
    ...(can('expenses:read') ? ['gastos' as View] : []),
    ...(can('receivables:read') ? ['cobranza' as View] : []),
    ...(can('accounts:read') ? ['cuentas' as View] : []),
    ...(can('suppliers:read') ? ['proveedores' as View] : []),
    ...(can('purchases:read') ? ['compras' as View] : []),
    ...(can('reports:read') ? ['reportes' as View] : []),
    ...(can('team:manage') ? ['catalogo' as View, 'equipo' as View, 'integraciones' as View, 'historial' as View] : []),
  ]), [can, clientAccount]);
  const title: Record<View, string> = { inicio: 'Resumen', clientes: 'Clientes', cotizaciones: 'Cotizaciones', ventas: 'Ventas y órdenes', seguimientos: 'Seguimientos', proyectos: 'Proyectos', instalaciones: 'Instalaciones', inventario: 'Inventario', gastos: 'Gastos operativos', cobranza: 'Cuentas por cobrar', cuentas: 'Caja y bancos', proveedores: 'Proveedores', compras: 'Compras y cuentas por pagar', reportes: 'Costeo por proyecto', catalogo: 'Catálogo de paquetes', equipo: 'Equipo y accesos', integraciones: 'Integraciones y respaldo', historial: 'History cards' };

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
      if (can('installations:read')) tasks.push(request<Project[]>('/projects', accessToken).then(setProjects));
      if (can('inventory:read')) tasks.push(request<InventoryItem[]>('/inventory', accessToken).then(setInventory));
      await Promise.all(tasks);
    } catch (error) {
      announce(error instanceof Error ? error.message : 'No se pudieron cargar los datos.', 'error');
    } finally { setLoading(false); }
  }, [accessToken, can]);

  useEffect(() => { const timer = window.setTimeout(() => setAuthResolved(true), 0); return () => window.clearTimeout(timer); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (allowedViews.length && !allowedViews.includes(view)) setView(allowedViews[0]); }, [allowedViews, view]);

  useEffect(() => {
    if (!accessToken || !can('customers:read') || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      setFollowupPushActive(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      const registration = await navigator.serviceWorker.getRegistration('/app/');
      const subscription = await registration?.pushManager.getSubscription();
      if (!subscription) { if (!cancelled) setFollowupPushActive(false); return; }
      const status = await request<{ active: boolean }>(`/push/subscriptions/self?endpoint=${encodeURIComponent(subscription.endpoint)}`, accessToken);
      if (!cancelled) setFollowupPushActive(status.active);
    })().catch(() => { if (!cancelled) setFollowupPushActive(false); });
    return () => { cancelled = true; };
  }, [accessToken, can]);

  async function toggleFollowupPush() {
    if (!accessToken || !('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      announce('Este navegador no admite avisos push en segundo plano.', 'error');
      return;
    }
    try {
      const existingRegistration = await navigator.serviceWorker.getRegistration('/app/');
      const existingSubscription = await existingRegistration?.pushManager.getSubscription();
      if (followupPushActive && existingSubscription) {
        const response = await fetch(`${apiBase}/push/subscriptions`, {
          method: 'DELETE', headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoint: existingSubscription.endpoint }),
        });
        if (!response.ok) throw new Error('No se pudo desactivar este dispositivo.');
        await existingSubscription.unsubscribe();
        setFollowupPushActive(false);
        announce('Avisos de seguimiento desactivados en este dispositivo.');
        return;
      }

      const permission = Notification.permission === 'granted' ? 'granted' : await Notification.requestPermission();
      if (permission !== 'granted') throw new Error('El navegador no autorizó los avisos.');
      const registration = await activeFieldServiceWorker();
      const keyResponse = await fetch(`${apiBase}/push/vapid-public-key`, { headers: { Authorization: `Bearer ${accessToken}` } });
      if (!keyResponse.ok) {
        const body = await keyResponse.json().catch(() => ({}));
        throw new Error(body.detail || 'No se pudo configurar el aviso push.');
      }
      const { public_key: publicKey } = await keyResponse.json();
      const applicationServerKey = Uint8Array.from(atob(publicKey.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - publicKey.length % 4) % 4)), char => char.charCodeAt(0));
      const subscription = await registration.pushManager.getSubscription() || await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey });
      const saveResponse = await fetch(`${apiBase}/push/subscriptions`, {
        method: 'POST', headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription.toJSON()),
      });
      if (!saveResponse.ok) {
        const body = await saveResponse.json().catch(() => ({}));
        throw new Error(body.detail || 'No se pudo guardar este dispositivo.');
      }
      setFollowupPushActive(true);
      announce('Avisos de seguimiento activados. Llegarán aunque cierres el CRM.');
    } catch (error) {
      announce(error instanceof Error ? error.message : 'No se pudieron activar los avisos.', 'error');
    }
  }

  useEffect(() => {
    if (!selectedCustomer || !accessToken || !can('customers:read')) { setActivities([]); return; }
    void request<Activity[]>(`/customers/${selectedCustomer.id}/activity`, accessToken).then(setActivities).catch(error => announce(error.message, 'error'));
  }, [selectedCustomer, accessToken, can]);

  useEffect(() => {
    if (!['equipo', 'instalaciones'].includes(view) || !accessToken || !can('team:manage')) return;
    setTeamLoading(true); setTeamError('');
    const teamRequest = request<TeamMember[]>('/team', accessToken).then(setTeam);
    const rolesRequest = view === 'equipo' ? request<RoleDefinition[]>('/team/roles', accessToken).then(setRoleDefinitions) : Promise.resolve();
    void Promise.all([teamRequest, rolesRequest]).catch(error => setTeamError(error.message || 'No se pudo cargar el equipo y sus permisos.')).finally(() => setTeamLoading(false));
  }, [view, accessToken, can]);

  useEffect(() => {
    if (view !== 'inventario' || !accessToken || !can('inventory:read')) return;
    void request<InventoryMovement[]>('/inventory/movements', accessToken)
      .then(setInventoryMovements)
      .catch(error => announce(error instanceof Error ? error.message : 'No se pudo cargar el kardex.', 'error'));
  }, [view, accessToken, can]);

  useEffect(() => {
    if (view !== 'gastos' || !accessToken || !can('expenses:read')) return;
    void request<ProjectExpense[]>('/expenses', accessToken).then(setExpenses)
      .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar los gastos.', 'error'));
    if (can('accounts:read')) void request<FinancialAccount[]>('/accounts', accessToken).then(setAccounts)
      .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las cuentas para gastos.', 'error'));
  }, [view, accessToken, can]);

  useEffect(() => {
    if (view === 'cuentas' && accessToken && can('accounts:read')) {
      void request<FinancialAccount[]>('/accounts', accessToken).then(rows => {
        setAccounts(rows);
        setSelectedAccountId(current => rows.some(row => row.id === current) ? current : rows[0]?.id || '');
      }).catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las cuentas.', 'error'));
    }
    if ((view === 'proveedores' || view === 'compras' || view === 'inventario') && accessToken && can('suppliers:read')) {
      void request<Supplier[]>('/suppliers', accessToken).then(setSuppliers)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar los proveedores.', 'error'));
    }
    if (view === 'compras' && accessToken && can('purchases:read')) {
      void request<Purchase[]>('/purchases', accessToken).then(setPurchases)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las compras.', 'error'));
      if (can('accounts:read')) void request<FinancialAccount[]>('/accounts', accessToken).then(setAccounts)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las cuentas de pago.', 'error'));
    }
    if (view === 'cobranza' && accessToken && can('receivables:read')) {
      void request<Receivable[]>('/receivables', accessToken).then(setReceivables)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudo cargar la cartera.', 'error'));
      if (can('accounts:read')) void request<FinancialAccount[]>('/accounts', accessToken).then(setAccounts)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las cuentas para cobranza.', 'error'));
    }
    if (view === 'ventas' && accessToken && can('sales:read')) {
      void request<Sale[]>('/sales', accessToken).then(setSales)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las ventas.', 'error'));
      if (can('installations:read')) void request<Installer[]>('/installers', accessToken).then(setInstallers)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudo cargar el equipo de instalación.', 'error'));
      if (can('inventory:read')) void request<InventoryItem[]>('/inventory', accessToken).then(setInventory)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudo cargar el almacén.', 'error'));
      if (can('accounts:read')) void request<FinancialAccount[]>('/accounts', accessToken).then(setAccounts)
        .catch(error => announce(error instanceof Error ? error.message : 'No se pudieron cargar las cuentas.', 'error'));
    }
  }, [view, accessToken, can]);

  useEffect(() => {
    if (view !== 'cuentas' || !selectedAccountId || !accessToken) { setAccountMovements([]); return; }
    void request<{ movements: CashMovement[] }>(`/accounts/${selectedAccountId}/movements`, accessToken)
      .then(payload => setAccountMovements(payload.movements))
      .catch(error => announce(error instanceof Error ? error.message : 'No se pudo cargar el estado de cuenta.', 'error'));
  }, [view, selectedAccountId, accessToken]);

  async function createExpense(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const payload = { project_id: String(data.get('project_id') || '') || null, installation_id: String(data.get('installation_id') || '') || null, account_id: String(data.get('account_id') || '') || null, category: String(data.get('category') || 'Otro'), expense_type: String(data.get('expense_type') || 'unclassified'), description: String(data.get('description') || '').trim(), amount: Number(data.get('amount')), occurred_on: String(data.get('occurred_on')), receipt_url: String(data.get('receipt_url') || '').trim() };
    const receipt = data.get('receipt_file');
    if (receipt instanceof File && receipt.size > 12 * 1024 * 1024) { announce('El comprobante debe pesar 12 MB o menos.', 'error'); return; }
    if (receipt instanceof File && !['application/pdf','image/jpeg','image/png','image/webp'].includes(receipt.type)) { announce('Adjunta un comprobante PDF, JPG, PNG o WebP.', 'error'); return; }
    try {
      const created = await request<ProjectExpense>('/expenses', accessToken, { method: 'POST', body: JSON.stringify(payload) });
      setExpenses(rows => [created, ...rows]);
      form.reset();
      if (receipt instanceof File && receipt.size) {
        await attachExpenseReceipt(created, receipt);
      } else announce('Gasto registrado y vinculado a su cuenta de caja o banco.');
      if (can('accounts:read')) setAccounts(await request<FinancialAccount[]>('/accounts', accessToken));
    }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar el gasto.', 'error'); }
  }

  async function attachExpenseReceipt(expense: ProjectExpense, file: File) {
    if (!accessToken) return;
    try {
      const saved = await request<{filename:string}>(`/expenses/${expense.id}/receipt-file`, accessToken, { method:'PUT', headers:{'Content-Type':file.type,'X-Document-Name':encodeURIComponent(file.name)}, body:file });
      setExpenses(rows => rows.map(row => row.id === expense.id ? {...row, receipt_available:true, receipt_drive_available:true, receipt_filename:saved.filename} : row));
      setPendingExpenseReceipt(null);
      announce('Gasto y comprobante archivados en Drive.');
    } catch (error) {
      setPendingExpenseReceipt({expense,file});
      const message = error instanceof Error ? error.message : 'error de conexión.';
      announce(`El gasto quedó registrado, pero el comprobante sigue pendiente: ${message === 'drive_not_configured' ? 'Google Drive todavía no está conectado en este entorno.' : message}`, 'error');
    }
  }

  async function downloadExpenseReceipt(expense: ProjectExpense) {
    if (!accessToken) return;
    try {
      const response = await fetch(`/api/v1/expenses/${expense.id}/receipt-file`, {headers:{Authorization:`Bearer ${accessToken}`}});
      if (!response.ok) { const body=await response.json().catch(()=>({})); throw new Error(body.detail||'No se pudo descargar el comprobante.'); }
      const url=URL.createObjectURL(await response.blob()); const link=document.createElement('a'); link.href=url; link.download=expense.receipt_filename||'comprobante'; link.click(); window.setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo descargar el comprobante.', 'error'); }
  }

  async function reverseExpense(expense: ProjectExpense, reason: string) {
    if (!accessToken) return;
    try {
      const correction = await request<ProjectExpense>(`/expenses/${expense.id}/reverse`, accessToken, { method: 'POST', body: JSON.stringify({ reason }) });
      setExpenses(rows => [correction, ...rows.map(row => row.id === expense.id ? { ...row, can_reverse: false } : row)]);
      if (can('accounts:read')) setAccounts(await request<FinancialAccount[]>('/accounts', accessToken));
      announce('Corrección registrada. El gasto original y sus efectos relacionados conservan historial.');
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo corregir el gasto.', 'error'); }
  }

  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget; const data = new FormData(form);
    const payload = { name: String(data.get('name') || '').trim(), account_type: String(data.get('account_type')), opening_balance: Number(data.get('opening_balance')), opening_balance_date: String(data.get('opening_balance_date')) };
    try { const row = await request<FinancialAccount>('/accounts', accessToken, { method: 'POST', body: JSON.stringify(payload) }); setAccounts(rows => [...rows, row].sort((a,b)=>a.name.localeCompare(b.name))); setSelectedAccountId(row.id); form.reset(); announce('Cuenta registrada con el saldo inicial indicado.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar la cuenta.', 'error'); }
  }

  async function createCashMovement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget; const data = new FormData(form);
    const payload = { account_id: selectedAccountId, direction: String(data.get('direction')), amount: Number(data.get('amount')), category: String(data.get('category')), description: String(data.get('description')), occurred_on: String(data.get('occurred_on')) };
    try { await request<CashMovement>('/cash-movements', accessToken, { method: 'POST', body: JSON.stringify(payload) }); const [rows, report] = await Promise.all([request<FinancialAccount[]>('/accounts', accessToken), request<{ movements: CashMovement[] }>(`/accounts/${selectedAccountId}/movements`, accessToken)]); setAccounts(rows); setAccountMovements(report.movements); form.reset(); announce('Movimiento registrado en la cuenta.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar el movimiento.', 'error'); }
  }

  async function transferCash(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget; const data = new FormData(form);
    const payload = { source_account_id: selectedAccountId, destination_account_id: String(data.get('destination_account_id') || ''), amount: Number(data.get('amount')), description: String(data.get('description') || '').trim(), occurred_on: String(data.get('occurred_on') || '') };
    try {
      await request('/cash-transfers', accessToken, { method: 'POST', body: JSON.stringify(payload) });
      const [rows, report] = await Promise.all([request<FinancialAccount[]>('/accounts', accessToken), request<{ movements: CashMovement[] }>(`/accounts/${selectedAccountId}/movements`, accessToken)]);
      setAccounts(rows); setAccountMovements(report.movements); form.reset(); announce('Transferencia registrada en las dos cuentas.');
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo transferir entre cuentas.', 'error'); }
  }

  async function reverseCashMovement(movement: CashMovement, reason: string) {
    if (!accessToken) return;
    try { await request<CashMovement>(`/cash-movements/${movement.id}/reverse`, accessToken, { method: 'POST', body: JSON.stringify({ reason }) }); const [rows, report] = await Promise.all([request<FinancialAccount[]>('/accounts', accessToken), request<{ movements: CashMovement[] }>(`/accounts/${selectedAccountId}/movements`, accessToken)]); setAccounts(rows); setAccountMovements(report.movements); announce('Corrección registrada con motivo y vínculo al movimiento original; se conservó el historial.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo corregir el movimiento.', 'error'); }
  }

  async function createSupplier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget; const data = new FormData(form);
    const payload = { name: String(data.get('name') || '').trim(), rfc: String(data.get('rfc') || '').trim(), phone: String(data.get('phone') || '').trim(), email: String(data.get('email') || '').trim(), payment_terms: String(data.get('payment_terms')), credit_days: Number(data.get('credit_days') || 0) };
    try { const row = await request<Supplier>('/suppliers', accessToken, { method: 'POST', body: JSON.stringify(payload) }); setSuppliers(rows => [...rows, row].sort((a,b)=>a.name.localeCompare(b.name))); form.reset(); announce('Proveedor guardado.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo guardar el proveedor.', 'error'); }
  }

  async function createReceivable(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!accessToken) return;
    const form = event.currentTarget; const data = new FormData(form);
    const payload = { customer_id: String(data.get('customer_id')), quote_id: String(data.get('quote_id') || '') || null, due_date: String(data.get('due_date')), amount: Number(data.get('amount')), installment_number: Number(data.get('installment_number') || 1), payment_method: String(data.get('payment_method') || 'Transferencia') };
    try { const created = await request<Receivable>('/receivables', accessToken, { method: 'POST', body: JSON.stringify(payload) }); setReceivables(rows => [created, ...rows]); form.reset(); announce('Saldo por cobrar registrado.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar el saldo.', 'error'); }
  }

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
    const assignedTo = String(form.get('assigned_to') || identity?.email || '').trim().toLowerCase();
    try { await request('/followups', accessToken, { method: 'POST', body: JSON.stringify({ customer_id: selectedCustomer.id, due_date: dueDate, note, assigned_to: assignedTo }) }); await refresh(); announce('Seguimiento programado y asignado.'); formElement.reset(); }
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
      const driveStatus = response.headers.get('X-Drive-Status');
      announce(driveStatus === 'saved' ? `PDF ${quote.folio} descargado y archivado en Drive.` : driveStatus === 'upload-failed' ? `PDF ${quote.folio} descargado; Drive no pudo archivarlo.` : `PDF ${quote.folio} descargado; Drive no está configurado y no se archivó.`, driveStatus === 'upload-failed' ? 'error' : 'success');
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo descargar el PDF.', 'error'); }
  }

  async function shareQuote(quote: Quote) {
    if (!quote.pricing_approved) { announce('Aprueba el precio del paquete antes de compartir la propuesta.', 'error'); return; }
    const phone = quote.customer?.phone?.replace(/\D/g, '') || '';
    const message = `Hola ${quote.customer?.name || ''}, te comparto la propuesta ${quote.folio} de Arco Energy por ${money(quote.total)}. Adjunto el PDF en esta conversación.`;
    setQuoteShareBusyId(quote.id); setQuoteShareError('');
    try {
      const response = await fetch(`${apiBase}/quotes/${quote.id}/pdf`, { headers: { Authorization: `Bearer ${accessToken}` } });
      if (!response.ok) throw new Error('No se pudo preparar el PDF para compartir.');
      const file = new File([await response.blob()], `${quote.folio}.pdf`, { type: 'application/pdf' });
      setPendingQuoteShare({ quote, file, message: phone ? message : `${message} Agrega el número o elige la conversación del cliente en WhatsApp.`, driveStatus: response.headers.get('X-Drive-Status') || 'unknown' });
      const driveNote = response.headers.get('X-Drive-Status') === 'saved' ? ' También quedó archivado en Drive.' : response.headers.get('X-Drive-Status') === 'upload-failed' ? ' Drive informó que no pudo archivar el archivo.' : ' Drive no está confirmado para este archivo.';
      announce(`PDF ${quote.folio} preparado. Elige cómo compartirlo.${driveNote}`, response.headers.get('X-Drive-Status') === 'upload-failed' ? 'info' : 'success');
    } catch (error) {
      announce(error instanceof Error ? error.message : 'No se pudo compartir la cotización.', 'error');
    } finally { setQuoteShareBusyId(''); }
  }

  async function sharePreparedQuote() {
    if (!pendingQuoteShare) return;
    const { quote, file, message } = pendingQuoteShare;
    if (!supportsPdfFileShare(file)) { setQuoteShareError('Este navegador no comparte archivos directamente. Usa la opción de descarga y WhatsApp.'); return; }
    try {
      await navigator.share({ files: [file], title: `Cotización ${quote.folio}`, text: message });
      setPendingQuoteShare(null); setQuoteShareError(''); announce('PDF compartido. Elige WhatsApp y la conversación abierta con el cliente.', 'success');
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') { setQuoteShareError('Compartir se canceló. Puedes intentar de nuevo o descargar el PDF y abrir WhatsApp.'); return; }
      setQuoteShareError('No se pudo abrir el selector de archivos compartidos. Prueba la opción de descarga y WhatsApp.');
    }
  }

  async function markQuoteSent(quote: Quote) {
    if (!quote.pricing_approved) { announce('Aprueba el catálogo comercial antes de marcar una propuesta como enviada.', 'error'); return; }
    if (!accessToken) return;
    try { await request(`/quotes/${quote.id}/status`, accessToken, { method: 'PATCH', body: JSON.stringify({ status: 'sent' }) }); await refresh(); announce('Cotización marcada como enviada.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo actualizar.', 'error'); }
  }

  async function acceptQuote(quote: Quote) {
    if (!accessToken) return;
    try { await request(`/quotes/${quote.id}/status`, accessToken, { method: 'PATCH', body: JSON.stringify({ status: 'accepted' }) }); await refresh(); announce(`Aceptación de ${quote.folio} registrada; ahora puedes preparar la venta y su orden.`); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar la aceptación.', 'error'); }
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
      setQuoteOpen(false); await refresh(); await downloadQuote(quote);
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
  const routePath = window.location.pathname.replace(/\/$/, '');
  const isLoginRoute = ['/login', '/crm/login'].includes(routePath);
  if (isLoginRoute && identity && accessToken) { window.location.replace(clientAccount ? '/app/' : '/crm/'); return null; }
  if (!identity || !accessToken) {
    if (!isLoginRoute) window.history.replaceState(null, '', '/crm/login');
    return <LoginScreen />;
  }
  if (isLoginRoute) { window.location.replace(clientAccount ? '/app/' : '/crm/'); return null; }
  if (clientAccount) { window.location.replace('/app/'); return null; }

  const nav: Array<[View, string, string]> = [['inicio', '◫', 'Resumen'], ['clientes', '♙', 'Clientes'], ['cotizaciones', '▤', 'Cotizaciones'], ...(can('sales:read') ? [['ventas', '▣', 'Ventas / OT']] as Array<[View, string, string]> : []), ['seguimientos', '◷', 'Seguimientos'], ...(can('installations:read') ? [['proyectos','▧','Proyectos'], ['instalaciones', '⌂', 'Instalaciones']] as Array<[View, string, string]> : []), ...(can('inventory:read') ? [['inventario', '▦', 'Inventario']] as Array<[View, string, string]> : []), ...(can('expenses:read') ? [['gastos', '$', 'Gastos']] as Array<[View, string, string]> : []), ...(can('receivables:read') ? [['cobranza', '↙', 'Cobranza']] as Array<[View, string, string]> : []), ...(can('accounts:read') ? [['cuentas', '▤', 'Caja / bancos']] as Array<[View, string, string]> : []), ...(can('suppliers:read') ? [['proveedores', '♧', 'Proveedores']] as Array<[View, string, string]> : []), ...(can('purchases:read') ? [['compras', '▤', 'Compras / CxP']] as Array<[View, string, string]> : []), ...(can('reports:read') ? [['reportes', '▥', 'Reportes']] as Array<[View, string, string]> : []), ...(can('team:manage') ? [['catalogo', '⊞', 'Catálogo'], ['equipo', '♧', 'Equipo'], ['integraciones', '☁', 'Drive / integraciones'], ['historial', '↺', 'History cards']] as Array<[View, string, string]> : [])];
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
        {view === 'cotizaciones' && <QuotesView quotes={quotes} onCreate={() => setQuoteOpen(true)} onDownload={downloadQuote} onShare={shareQuote} shareBusyId={quoteShareBusyId} onMarkSent={markQuoteSent} onAccept={acceptQuote} canWrite={can('quotes:write')} />}
        {view === 'ventas' && <SalesView items={sales} quotes={quotes} inventory={inventory} installers={installers} accounts={accounts} canWrite={can('sales:write')} token={accessToken || ''} onItems={setSales} onAccounts={setAccounts} onInventory={setInventory} onRefresh={refresh} announce={announce} />}
        {view === 'seguimientos' && <FollowupsView items={followups} onComplete={completeFollowup} onCustomer={setSelectedCustomer} pushActive={followupPushActive} onTogglePush={()=>void toggleFollowupPush()} pushSupported={'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window} />}
        {view === 'proyectos' && <ProjectsView items={projects} customers={customers} canWrite={can('installations:write')} token={accessToken || ''} onRefresh={refresh} announce={announce} />}
        {view === 'instalaciones' && <InstallationsView items={installations} projects={projects} customers={customers} team={team} canWrite={can('installations:write')} token={accessToken || ''} onRefresh={refresh} announce={announce} />}
        {view === 'inventario' && <InventoryView items={inventory} movements={inventoryMovements} installations={installations} installers={installers} suppliers={suppliers} canManage={can('inventory:manage')} canIssue={can('inventory:issue')} canReadCosts={can('inventory:costs:read') || can('inventory:manage')} token={accessToken || ''} onRefresh={refresh} onMovements={setInventoryMovements} onInstallations={setInstallations} announce={announce} />}
        {view === 'gastos' && <ExpensesView items={expenses} installations={installations} projects={projects} accounts={accounts} canWrite={can('expenses:write')} canCorrect={can('expenses:write') && !identity.roles.includes('instalador')} onSubmit={createExpense} onReverse={reverseExpense} onDownloadReceipt={downloadExpenseReceipt} pendingReceipt={pendingExpenseReceipt} onRetryReceipt={()=>pendingExpenseReceipt&&void attachExpenseReceipt(pendingExpenseReceipt.expense,pendingExpenseReceipt.file)} />}
        {view === 'cobranza' && <ReceivablesView items={receivables} customers={customers} quotes={quotes} accounts={accounts} canWrite={can('receivables:write')} token={accessToken || ''} onCreate={createReceivable} onItems={setReceivables} onAccounts={setAccounts} announce={announce} />}
        {view === 'cuentas' && <AccountsView accounts={accounts} selectedId={selectedAccountId} onSelect={setSelectedAccountId} movements={accountMovements} canManage={can('accounts:manage')} canWrite={can('accounts:write')} onCreateAccount={createAccount} onCreateMovement={createCashMovement} onTransfer={transferCash} onReverse={reverseCashMovement} />}
        {view === 'proveedores' && <SuppliersView items={suppliers} canWrite={can('suppliers:manage')} onSubmit={createSupplier} />}
        {view === 'compras' && <PurchasesView items={purchases} suppliers={suppliers} inventory={inventory} accounts={accounts} canWrite={can('purchases:write')} token={accessToken || ''} onItems={setPurchases} onSuppliers={setSuppliers} onAccounts={setAccounts} onInventory={setInventory} announce={announce} />}
        {view === 'reportes' && <><OperationsReportView token={accessToken || ''} /><ProfitabilityView token={accessToken || ''} installations={installations} projects={projects} canManageAdjustments={can('accounts:manage')} /></>}
        {view === 'catalogo' && <CatalogView catalog={catalog} onSave={savePackage} onLogin={() => window.location.assign('/crm/login')} />}
        {view === 'equipo' && <TeamView members={team} roleDefinitions={roleDefinitions} loading={teamLoading} error={teamError} name={teamName} email={teamEmail} password={teamPassword} role={teamRole} busy={teamBusy} onName={setTeamName} onEmail={setTeamEmail} onPassword={setTeamPassword} onRole={setTeamRole} onSubmit={createMember} onUpdateRole={updateMemberRole} />}
        {view === 'integraciones' && <IntegrationsView token={accessToken || ''} />}
        {view === 'historial' && <HistoryCardsView token={accessToken || ''} announce={announce} />}

        <footer className="page-foot"><span>Arco Energy · CRM</span><span>La información se actualiza desde el espacio de trabajo de Arco Energy.</span></footer>
      </div>
    </main>

    <button className={`agent-launcher ${agentOpen ? 'open' : ''}`} onClick={() => setAgentOpen(value => !value)} aria-label={agentOpen ? 'Cerrar asistente' : 'Abrir asistente'}>{agentOpen ? '×' : '✦'}</button>
    <aside className="agent-panel" hidden={!agentOpen} aria-hidden={!agentOpen}><div className="agent-panel-head"><div><span className="agent-spark">✦</span><div><b>Asistente Arco</b><small>Consulta clientes y paquetes autorizados</small></div></div><button onClick={() => setAgentOpen(false)} aria-label="Cerrar asistente">×</button></div><AgentChat title="¿Qué neces…27089 tokens truncated…nea o captura el código"/><Field label="Unidad" name="unit" required defaultValue="pieza" placeholder="pieza, metro, par"/><Field label="Existencia inicial" name="initial_quantity" type="number" min="0" step="0.01" defaultValue={0}/><Field label="Mínimo de alerta" name="minimum_quantity" type="number" min="0" step="0.01" defaultValue={0}/><label className="field"><span>Responsable de reposición</span><select name="restock_responsible_email" defaultValue=""><option value="">Sin asignar</option>{installers.map(person=><option key={person.email} value={person.email}>{person.name} · {person.email}</option>)}</select><small>Recibirá un aviso push al bajar del mínimo, si activó notificaciones en la PWA.</small></label><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" defaultValue={0}/><button className="button button-primary">Agregar artículo</button></form><form className="team-form" onSubmit={event=>void submit(event,'/inventory/receive')}><h3>Entrada de almacén</h3><label className="field"><span>Artículo</span><select name="item_id" required><option value="">Selecciona material</option>{items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Cantidad recibida" name="quantity" type="number" min="0.01" step="0.01" required/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" required/><Field label="Referencia" name="reason" placeholder="Factura, proveedor o nota"/><button className="button button-primary">Registrar entrada</button></form></div>}<div className="data-table-wrap"><table className="data-table"><thead><tr><th>ARTÍCULO</th><th>EXISTENCIA</th><th>MÍNIMO</th>{canReadCosts&&<th>COSTO UNITARIO</th>}</tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.name}<small className="sub-cell">{[item.category,item.subcategory,item.brand,item.model].filter(Boolean).join(" · ") || item.description || item.unit}</small>{item.supplier_id&&<small className="sub-cell">Proveedor: {suppliers.find(supplier=>supplier.id===item.supplier_id)?.name||"sin nombre"}</small>}{item.barcode&&<small className="sub-cell">Código: {item.barcode}</small>}{item.restock_responsible_email&&<small className="sub-cell">Reabasto: {item.restock_responsible_email}</small>}{canManage&&<div className="inventory-item-actions"><button type="button" className="text-action inventory-label-action" onClick={()=>setEditingItem(item)}>Editar ficha</button><button type="button" className="text-action inventory-label-action" onClick={()=>setLabelItem(item)}>Imprimir QR</button></div>}</td><td>{item.available_quantity ?? item.quantity} {item.unit}<small className="sub-cell">{item.reserved_quantity ? `${item.reserved_quantity} asignados a órdenes` : `${item.quantity} físicos`}</small></td><td>{item.minimum_quantity}</td>{canReadCosts&&<td>{money(item.unit_cost)}</td>}</tr>)}</tbody></table>{!items.length&&<EmptyState title="Almacén sin artículos" body="Crea el catálogo de materiales reales para empezar a registrar existencias."/>}</div></section><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">KARDEX · {movements.length} MOVIMIENTOS CARGADOS</span><h2>Historial de almacén</h2></div><div className="heading-actions"><button className="button button-outline" disabled={loadingMovements} onClick={()=>void refreshMovements()}>{loadingMovements?'Actualizando…':'Actualizar'}</button><button className="button button-outline" disabled={exportingMovements} onClick={()=>void exportMovements()}>{exportingMovements?'Exportando todo…':'Descargar CSV completo'}</button></div></div><form className="kardex-filter" onSubmit={event=>void filterMovements(event)}><label>Artículo<select value={movementItem} onChange={event=>setMovementItem(event.target.value)}><option value="">Todos los artículos</option>{items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Desde<input type="date" value={movementFrom} onChange={event=>setMovementFrom(event.target.value)}/></label><label>Hasta<input type="date" value={movementTo} onChange={event=>setMovementTo(event.target.value)}/></label><button className="button button-outline" disabled={loadingMovements}>{loadingMovements?'Consultando…':'Filtrar'}</button></form><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>ARTÍCULO</th><th>MOVIMIENTO</th><th>CAMBIO</th>{canReadCosts&&<th>COSTO UNITARIO</th>}<th>REFERENCIA</th></tr></thead><tbody>{movements.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-MX')}</td><td>{row.item_name}<small className="sub-cell">{row.created_by}</small></td><td>{row.movement_type==='out'?'Salida':row.movement_type==='consumption'?'Consumo confirmado':row.movement_type==='consumption_return'?'Consumo corregido':row.movement_type==='waste'?'Merma':row.movement_type==='return'?'Devolución':row.movement_type==='damage'?'Merma por daño':row.movement_type==='receipt_reversal'?'Reversa de entrada':row.movement_type==='purchase_reversal'?'Reversa de compra':'Entrada'}</td><td>{row.signed_quantity>0?'+':''}{row.signed_quantity} {row.unit}</td>{canReadCosts&&<td>{row.unit_cost===null||row.unit_cost===undefined?'Sin dato':money(row.unit_cost)}</td>}<td>{row.reason||'—'}{row.related_movement_id&&<small className="sub-cell">Relacionado con {row.related_movement_id.slice(0,8)}</small>}{canManage&&row.can_reverse&&<button type="button" className="text-action inventory-label-action" onClick={()=>void reverseReceipt(row)}>Corregir entrada</button>}</td></tr>)}</tbody></table>{!movements.length&&<EmptyState title="Sin movimientos registrados" body="Las entradas y consumos aparecerán aquí con fecha, responsable y referencia."/>}</div>{hasMoreMovements&&<div className="table-pagination"><span>Mostrando {movements.length} movimientos; hay más por cargar.</span><button className="button button-outline" onClick={()=>void loadMoreMovements()} disabled={loadingMovements}>{loadingMovements?'Cargando…':'Cargar siguientes 500'}</button></div>}</section></div>{editingItem&&<Modal title="Editar material" subtitle="Corrige la ficha del catálogo; el saldo físico solo cambia mediante movimientos de almacén." onClose={()=>setEditingItem(null)} wide><form className="form-grid" onSubmit={event=>void updateCatalogItem(event)}><Field label="Nombre del material" name="name" required defaultValue={editingItem.name}/><Field label="Unidad" name="unit" required defaultValue={editingItem.unit}/><label className="field span-two"><span>Descripción</span><textarea name="description" maxLength={1000} defaultValue={editingItem.description||""}/></label><Field label="Categoría" name="category" defaultValue={editingItem.category||""}/><Field label="Subcategoría" name="subcategory" defaultValue={editingItem.subcategory||""}/><Field label="Marca" name="brand" defaultValue={editingItem.brand||""}/><Field label="Modelo" name="model" defaultValue={editingItem.model||""}/><label className="field"><span>Proveedor habitual</span><select name="supplier_id" defaultValue={editingItem.supplier_id||""}><option value="">Sin proveedor asignado</option>{suppliers.filter(item=>item.active).map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Código QR / barras" name="barcode" maxLength={120} defaultValue={editingItem.barcode||""}/><Field label="Mínimo de alerta" name="minimum_quantity" type="number" min="0" step="0.01" defaultValue={editingItem.minimum_quantity}/><label className="field"><span>Responsable de reposición</span><select name="restock_responsible_email" defaultValue={editingItem.restock_responsible_email||""}><option value="">Sin asignar</option>{installers.map(person=><option key={person.email} value={person.email}>{person.name} · {person.email}</option>)}</select><small>Recibirá un aviso push al bajar del mínimo, si activó notificaciones en la PWA.</small></label><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" defaultValue={editingItem.unit_cost}/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={()=>setEditingItem(null)}>Cancelar</button><button className="button button-primary">Guardar cambios</button></div></form></Modal>}{labelItem&&<div className="inventory-label-overlay"><section className="inventory-label-card"><button className="inventory-label-close" onClick={()=>setLabelItem(null)} aria-label="Cerrar etiqueta">×</button><QRCodeSVG value={labelCode} size={220} level="M" includeMargin/><h2>{labelItem.name}</h2><p>{labelItem.category||labelItem.brand||"Artículo de ArcoEnergy"}</p><code>{labelCode}</code><div className="inventory-label-actions"><button className="button button-outline" onClick={()=>window.print()}>Imprimir etiqueta</button><button className="button button-primary" onClick={()=>setLabelItem(null)}>Cerrar</button></div></section></div>}</>;
}

function ProfitabilityView({ token, installations, projects, canManageAdjustments }: { token: string; installations:Installation[]; projects:Project[]; canManageAdjustments:boolean }) {
  const now = new Date();
  const [month, setMonth] = useState(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
  const [projectId, setProjectId] = useState('');
  const [report, setReport] = useState<ProfitabilityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [adjustments, setAdjustments] = useState<ProfitabilityAdjustment[]>([]);
  const [adjustmentMessage, setAdjustmentMessage] = useState('');

  useEffect(() => {
    if (!token) return;
    let active = true;
    setLoading(true); setError('');
    const query = new URLSearchParams({ month });
    if (projectId) query.set('project_id', projectId);
    request<ProfitabilityReport>(`/reports/profitability?${query}`, token)
      .then(result => { if (active) setReport(result); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'No se pudo cargar el reporte.'); })
      .finally(() => { if (active) setLoading(false); });
    request<ProfitabilityAdjustment[]>(`/profitability-adjustments?${query}`, token)
      .then(result => { if (active) setAdjustments(result); })
      .catch(reason => { if (active) setAdjustmentMessage(reason instanceof Error ? reason.message : 'No se cargaron las devoluciones y bonificaciones.'); });
    return () => { active = false; };
  }, [token, month, projectId, refreshKey]);

  return <div className="dashboard-grid">
    <section className="surface-card table-surface">
      <div className="table-toolbar"><div><span className="eyebrow">RESULTADO OPERATIVO PRELIMINAR</span><h2>Por proyecto y mes</h2></div><button className="button button-outline" onClick={() => setRefreshKey(value => value + 1)} disabled={loading}>{loading ? 'Actualizando…' : 'Actualizar'}</button></div>
      <form className="kardex-filter" onSubmit={event => { event.preventDefault(); setRefreshKey(value => value + 1); }}><label>Periodo<input type="month" value={month} onChange={event => setMonth(event.target.value)} required/></label><label>Proyecto<select aria-label="Filtrar resultado por proyecto" value={projectId} onChange={event => setProjectId(event.target.value)}><option value="">Todos los proyectos</option>{projects.map(project=><option key={project.id} value={project.id}>{project.code} · {project.name}</option>)}</select></label><button className="button button-primary" disabled={loading}>Consultar</button></form>
      {error && <p role="alert" className="error-message">{error}</p>}
      {report && <>
        <div className="notice warning"><b>Reporte preliminar</b><span>Ventas − costo de material consumido − gastos + devoluciones y bonificaciones capturadas. Los ajustes se conservan en una bitácora separada y no generan por sí solos movimientos de caja ni modifican ventas; no es un estado contable formal.</span></div>
        <p className="muted-copy">{report.basis} · {report.totals.missing_cost_movements ? `${report.totals.missing_cost_movements} consumos sin costo unitario` : 'Todos los consumos del periodo tienen costo unitario registrado.'}</p>
        <section className="stats"><article><small>VENTAS REGISTRADAS</small><strong>{money(report.totals.sales)}</strong><span>Fecha de registro de venta</span></article><article><small>COSTO DE MATERIAL CONSUMIDO</small><strong>{report.totals.materials_cost === null ? 'Sin costo completo' : money(report.totals.materials_cost)}</strong><span>Por fecha de confirmación</span></article><article><small>GASTOS CAPTURADOS</small><strong>{money(report.totals.expenses)}</strong><span>Fijos {money(report.totals.expenses_by_type.fixed)} · variables {money(report.totals.expenses_by_type.variable)} · fecha capturada</span></article><article><small>DEVOLUCIONES Y BONIFICACIONES (+)</small><strong>{money(report.totals.returns_and_bonifications)}</strong><span>Devoluciones {money(report.totals.adjustments_by_type.return)} · bonificaciones {money(report.totals.adjustments_by_type.bonification)}</span></article><article><small>RESULTADO PRELIMINAR</small><strong>{report.totals.preliminary_result === null ? 'Incompleto' : money(report.totals.preliminary_result)}</strong><span>Incluye ajustes registrados</span></article></section>
        <div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROYECTO / ORDEN</th><th>CIUDAD</th><th>VENTAS</th><th>COSTO MATERIAL</th><th>GASTOS</th><th>DEV. / BONIF. (+)</th><th>RESULTADO PRELIMINAR</th></tr></thead><tbody>{report.rows.map(row => <tr key={row.project_id || row.installation_id || 'unassigned'}><td>{row.project}<small className="sub-cell">{row.project_code ? `${row.project_code} · ` : ''}{row.folio || 'Sin orden de trabajo'}</small></td><td>{row.city || '—'}</td><td>{money(row.sales)}</td><td>{row.materials_cost === null ? 'Costo pendiente' : money(row.materials_cost)}{row.missing_cost_movements > 0 && <small className="sub-cell">{row.missing_cost_movements} movimientos sin costo</small>}</td><td>{money(row.expenses)}<small className="sub-cell">Fijos {money(row.expenses_by_type.fixed)} · variables {money(row.expenses_by_type.variable)}{row.expenses_by_type.unclassified ? ` · sin clasificar ${money(row.expenses_by_type.unclassified)}` : ''}</small><small className="sub-cell">{Object.entries(row.expenses_by_category).map(([category, amount]) => `${category}: ${money(amount)}`).join(' · ')}</small></td><td>{money(row.returns_and_bonifications)}</td><td><b>{row.preliminary_result === null ? 'Incompleto' : money(row.preliminary_result)}</b></td></tr>)}</tbody></table>{report.rows.length === 0 && <EmptyState title="Sin movimientos en el periodo" body="El reporte aparecerá cuando haya ventas, consumo de materiales o gastos reales en el mes seleccionado."/>}</div>
        <section className="panel"><div className="panel-head"><div><h2>Devoluciones y bonificaciones</h2><p>Registro independiente para el resultado preliminar. No afecta caja ni cambia las ventas.</p></div></div>
          {canManageAdjustments && <form className="form-grid" onSubmit={async event => { event.preventDefault(); const form = new FormData(event.currentTarget); try { await request('/profitability-adjustments', token, {method:'POST', body:JSON.stringify({installation_id:String(form.get('installation_id')||'')||null, adjustment_type:String(form.get('adjustment_type')), description:String(form.get('description')), amount:Number(form.get('amount')), occurred_on:String(form.get('occurred_on'))})}); event.currentTarget.reset(); setRefreshKey(value=>value+1); setAdjustmentMessage('Ajuste registrado en la bitácora.'); } catch(reason) { setAdjustmentMessage(reason instanceof Error ? reason.message : 'No se pudo registrar el ajuste.'); } }}><label className="field"><span>Tipo</span><select name="adjustment_type"><option value="return">Devolución</option><option value="bonification">Bonificación</option></select></label><label className="field"><span>Proyecto / orden (opcional)</span><select name="installation_id"><option value="">Sin proyecto</option>{installations.map(item=><option key={item.id} value={item.id}>{item.folio || 'Orden'} · {item.customer?.name || 'Cliente'}</option>)}</select></label><label className="field"><span>Descripción</span><input name="description" minLength={3} maxLength={240} required /></label><label className="field"><span>Importe MXN</span><input name="amount" type="number" min="0.01" step="0.01" required /></label><label className="field"><span>Fecha</span><input name="occurred_on" type="date" defaultValue={cancunDate()} required /></label><div className="modal-actions"><button className="button button-primary">Registrar ajuste</button></div></form>}
          {adjustmentMessage && <p role="status">{adjustmentMessage}</p>}{adjustments.map(item=><div className="follow-row" key={item.id}><div className="follow-info"><b>{item.adjustment_type==='return'?'Devolución':'Bonificación'} · {item.project}</b><small>{item.folio || item.occurred_on} · {item.description}</small></div><strong>{money(item.amount)}</strong>{canManageAdjustments && item.can_reverse && <button className="row-action" onClick={async()=>{const reason=window.prompt('Motivo de la corrección (mínimo 5 caracteres):');if(!reason)return;try{await request(`/profitability-adjustments/${item.id}/reverse`,token,{method:'POST',body:JSON.stringify({reason})});setRefreshKey(value=>value+1);setAdjustmentMessage('Corrección registrada como un nuevo movimiento.')}catch(error){setAdjustmentMessage(error instanceof Error?error.message:'No se pudo corregir el ajuste.')}}}>Corregir</button>}</div>)}{adjustments.length===0&&<p className="muted-copy">Sin ajustes en este periodo.</p>}
        </section>
      </>}
    </section>
  </div>;
}

function IntegrationsView({ token }: { token: string }) {
  const [drive, setDrive] = useState<{ connected: boolean; status: string; folder_name?: string; business_snapshot_available?: boolean; business_snapshot_schedule?: { enabled: boolean; interval_hours: number; status: string; last_attempt_at?: string | null; last_success_at?: string | null; next_due_at?: string | null; last_filename?: string | null; last_error_code?: string | null } } | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [savedFile, setSavedFile] = useState<{ filename: string; record_count: number; bytes: number } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await request<{ google_drive: typeof drive }>('/integrations', token);
      setDrive(result.google_drive);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo consultar Drive.');
    } finally { setLoading(false); }
  }, [token]);
  useEffect(() => { void load(); }, [load]);

  async function exportData() {
    setExporting(true);
    setError('');
    setSavedFile(null);
    try {
      const result = await request<{ saved: boolean; filename: string; record_count: number; bytes: number }>(
        '/integrations/google-drive/business-snapshot', token, { method: 'POST' },
      );
      setSavedFile(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el archivo en Drive.');
    } finally { setExporting(false); }
  }

  const connected = Boolean(drive?.connected);
  const connectionLabel = loading ? 'Consultando conexión…' : connected
    ? `Conectado${drive?.folder_name ? ` · ${drive.folder_name}` : ''}`
    : drive?.status === 'folder_not_configured' ? 'Pendiente: falta configurar la carpeta privada'
      : drive?.status === 'credentials_not_configured' ? 'Pendiente: faltan credenciales de servicio'
        : 'Sin conexión · revisa carpeta y permisos de Drive';

  return <div className="page-content">
    <div className="page-heading"><div><span className="eyebrow">ADMINISTRACIÓN / DATOS</span><h1>Integraciones y respaldo</h1><p>Revisa las conexiones externas y la copia periódica de los datos empresariales.</p></div><button className="button button-outline" onClick={() => void load()} disabled={loading}>{loading ? 'Consultando…' : 'Actualizar estado'}</button></div>
    <div className="dashboard-grid">
      <section className="surface-card table-surface">
        <div className="section-title"><div><span className="eyebrow">ALMACENAMIENTO PRIVADO</span><h2>Google Drive</h2></div><span className={`status-chip ${connected ? 'status-approved' : 'status-overdue'}`}>{connected ? 'Conectado' : 'Pendiente'}</span></div>
        <p className="muted-copy">{connectionLabel}</p>
        <div className="integration-data-list"><p><b>Respaldo automático:</b> {drive?.business_snapshot_schedule?.enabled ? `cada ${drive.business_snapshot_schedule.interval_hours} h. ` : 'Pendiente de configurar Drive. '}{drive?.business_snapshot_schedule?.last_success_at ? `Último respaldo correcto: ${new Date(drive.business_snapshot_schedule.last_success_at).toLocaleString('es-MX')}.` : 'Aún no hay un respaldo automático confirmado.'}{drive?.business_snapshot_schedule?.status === 'failed' && ' El último intento falló; el sistema reintentará automáticamente.'}</p><p><b>Exportación manual:</b> JSON descargable, máximo 64 MB; se genera al solicitarla y se guarda en la carpeta privada configurada.</p><p><b>Historial incluido:</b> clientes, cotizaciones, proyectos, órdenes, inventario, movimientos, compras, pagos, cuentas, gastos, ajustes, history cards y perfiles/roles del equipo.</p><p><b>Datos excluidos:</b> hashes de contraseña, tokens de sesión, credenciales y metadatos de integración, claves/endpoints push y recibos técnicos de sincronización offline.</p></div>
        <div className="notice warning"><b>Datos sensibles</b><span>La exportación contiene información de contacto y financiera. Mantén la carpeta de Drive compartida solo con personal autorizado.</span></div>
        {savedFile && <p className="notice success" role="status">Archivo guardado en Drive: <b>{savedFile.filename}</b> · {savedFile.record_count.toLocaleString('es-MX')} registros · {(savedFile.bytes / 1024 / 1024).toFixed(2)} MB.</p>}
        {error && <p className="error-message" role="alert">{error}</p>}
        <button className="button button-primary" onClick={() => void exportData()} disabled={!connected || exporting || loading}>{exporting ? 'Exportando datos…' : 'Guardar exportación en Drive'}</button>
        {!connected && <small className="muted-copy">Configura la carpeta privada y la cuenta de servicio desde Factory para habilitar la exportación.</small>}
      </section>
      <section className="surface-card table-surface">
        <span className="eyebrow">CANALES DE CONTACTO</span><h2>WhatsApp</h2><p className="muted-copy">Disponible como click-to-chat. El equipo abre la conversación y adjunta los documentos; el sistema no envía mensajes automáticamente.</p>
        <hr/><span className="eyebrow">DOCUMENTACIÓN</span><h2>Contratos y firma electrónica</h2><p className="muted-copy">Pendiente de plantillas legales aprobadas, política de privacidad y selección de proveedor para firma y verificación.</p>
      </section>
    </div>
  </div>;
}

function HistoryCardsView({ token, announce }: { token: string; announce: (message: string, type?: Notice['type']) => void }) {
  const [cards, setCards] = useState<Array<{ id:string; story_id:string; version:number; iteration:string; stakeholder:string; source_literal:string; source_type:string; source_reference:string; source_artifact:{artifacts:Array<{artifact_type:string;reference:string;channel:string;location:string;sha256?:string|null}>}; source_language:string; source_attribution:string; source_occurred_at?:string|null; source_confidence:string; source_links:Array<{artifact_index:number;relation:string;location:string}>; normalized_story:string; acceptance_criteria:string[]; unresolved_questions:string[]; created_at:string }>>([]);
  const [error, setError] = useState('');
  const load = async () => { try { setCards(await request<Array<{ id:string; story_id:string; version:number; iteration:string; stakeholder:string; source_literal:string; source_type:string; source_reference:string; source_artifact:{artifacts:Array<{artifact_type:string;reference:string;channel:string;location:string;sha256?:string|null}>}; source_language:string; source_attribution:string; source_occurred_at?:string|null; source_confidence:string; source_links:Array<{artifact_index:number;relation:string;location:string}>; normalized_story:string; acceptance_criteria:string[]; unresolved_questions:string[]; created_at:string }>>('/history-cards', token)); setError(''); } catch(e) { setError(e instanceof Error?e.message:'No se pudieron cargar las tarjetas.'); } };
  useEffect(() => { void load(); }, [token]);
  async function append(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form=event.currentTarget; const fields=new FormData(form); const id=String(fields.get('story_id')).trim(); const versions=cards.filter(card=>card.story_id===id).map(card=>card.version); const payload={story_id:id,version:Math.max(0,...versions)+1,iteration:String(fields.get('iteration')),stakeholder:String(fields.get('stakeholder')),source_literal:String(fields.get('source_literal')),source_type:String(fields.get('source_type')),source_reference:String(fields.get('source_reference')),source_artifacts:[{artifact_type:String(fields.get('source_type')),reference:String(fields.get('source_reference')),channel:String(fields.get('source_channel')||fields.get('source_type')),location:String(fields.get('artifact_location')||''),sha256:String(fields.get('source_sha256')||'')||null}],source_links:[{artifact_index:0,relation:String(fields.get('source_relation')),location:String(fields.get('source_location')||'')}],source_language:String(fields.get('source_language')||'es'),source_attribution:String(fields.get('source_attribution')||fields.get('stakeholder')),source_occurred_at:String(fields.get('source_occurred_at')||'')||null,source_confidence:String(fields.get('source_confidence')),normalized_story:String(fields.get('normalized_story')),acceptance_criteria:String(fields.get('acceptance_criteria')).split('\n').map(x=>x.trim()).filter(Boolean),unresolved_questions:String(fields.get('unresolved_questions')).split('\n').map(x=>x.trim()).filter(Boolean),linked_cards:String(fields.get('linked_cards')).split(',').map(x=>x.trim()).filter(Boolean)}; try { await request('/history-cards',token,{method:'POST',body:JSON.stringify(payload)}); await load(); form.reset(); announce(`Nueva versión guardada para ${id}.`); } catch(e) { announce(e instanceof Error?e.message:'No se pudo guardar la tarjeta.','error'); } }
  return <div className="dashboard-grid"><section className="surface-card table-surface"><div className="section-title"><div><span className="eyebrow">DISCOVERY · REGISTRO INMUTABLE</span><h2>Agregar iteración</h2></div></div><p className="muted-copy">El relato fuente se guarda literal. Las correcciones crean una nueva versión; las anteriores no se sobrescriben.</p><form className="team-form" onSubmit={append}><Field label="ID de la tarjeta" name="story_id" required placeholder="US-43"/><Field label="Iteración" name="iteration" required placeholder="Iteración 2 · 2026-11-06"/><Field label="Stakeholder" name="stakeholder" required/><label className="field"><span>Tipo de fuente</span><select name="source_type" required><option value="">Selecciona</option><option>WhatsApp</option><option>Documento</option><option>Audio transcrito</option><option>Imagen</option><option>Entrevista</option><option>Validación</option></select></label><label className="field span-two"><span>Relato literal (obligatorio)</span><textarea name="source_literal" required minLength={3}/></label><Field className="span-two" label="Referencia durable del artefacto" name="source_reference" required placeholder="Ruta privada, URL o ID autorizado"/><div className="form-grid span-two"><Field label="Canal de origen" name="source_channel" placeholder="WhatsApp, Word, correo"/><Field label="Ubicación exacta" name="artifact_location" placeholder="Mensaje, página o minuto"/><Field label="SHA-256 del artefacto (opcional)" name="source_sha256" maxLength={64}/><Field label="Idioma" name="source_language" required defaultValue="es"/><Field label="Atribución del relato" name="source_attribution" placeholder="Autor o transcriptor"/><Field label="Fecha/hora original si se conoce" name="source_occurred_at" placeholder="2026-11-07T15:20:00-06:00"/><label className="field"><span>Fidelidad del relato</span><select name="source_confidence" required defaultValue="needs_validation"><option value="verbatim">Cita literal revisada</option><option value="transcription">Transcripción de audio</option><option value="paraphrase">Paráfrasis identificada</option><option value="reconstruction">Reconstrucción</option><option value="needs_validation">Pendiente de validar</option></select></label><label className="field"><span>Relación con la fuente</span><select name="source_relation" required defaultValue="literal"><option value="literal">Cita literal</option><option value="transcription">Transcripción</option><option value="paraphrase">Paráfrasis</option><option value="inference">Inferencia del equipo</option><option value="validation">Validación explícita</option><option value="reconstruction">Reconstrucción</option></select></label><Field label="Ubicación del fragmento citado" name="source_location" placeholder="Mensaje 4, apartado 2, 00:35"/></div><label className="field span-two"><span>Historia normalizada</span><textarea name="normalized_story" required/></label><label className="field span-two"><span>Criterios (uno por línea)</span><textarea name="acceptance_criteria"/></label><label className="field span-two"><span>Preguntas abiertas (una por línea)</span><textarea name="unresolved_questions"/></label><Field className="span-two" label="Tarjetas relacionadas (separadas por coma)" name="linked_cards"/><button className="button button-primary">Guardar versión</button></form></section><section className="surface-card table-surface"><div className="section-title"><div><span className="eyebrow">HISTORIAL APPEND-ONLY</span><h2>{cards.length} versiones</h2></div><button className="button button-outline" onClick={()=>void load()}>Actualizar</button></div>{error&&<p role="alert" className="error-message">{error}</p>}{cards.length?cards.map(card=><article className="focus-row" key={card.id}><div><b>{card.story_id} · v{card.version}</b><small>{card.iteration} · {card.stakeholder} · {card.source_type}</small><p>{card.normalized_story}</p><details><summary>Ver relato original</summary><blockquote>{card.source_literal}</blockquote><small>{card.source_attribution} · {card.source_language} · Fidelidad: {card.source_confidence}{card.source_occurred_at ? ` · ${card.source_occurred_at}` : ""}</small><ul>{(card.source_artifact?.artifacts||[]).map((artifact,index)=><li key={`${artifact.reference}-${index}`}>{artifact.artifact_type} · {artifact.channel} · {artifact.reference}{artifact.location ? ` · ${artifact.location}` : ""}{artifact.sha256 ? ` · SHA-256 ${artifact.sha256}` : ""}</li>)}</ul><small>Relaciones: {(card.source_links||[]).map(link=>`${link.relation}${link.location ? ` (${link.location})` : ""}`).join(" · ")}</small></details></div></article>):!error&&<EmptyState title="Sin tarjetas registradas en la base de datos" body="Las tarjetas y fuentes del discovery inicial siguen en docs/discovery/history-cards.md. Usa este formulario para registrar nuevas versiones."/>}</section></div>;
}

function ProjectsView({ items, customers, canWrite, token, onRefresh, announce }: { items:Project[]; customers:Customer[]; canWrite:boolean; token:string; onRefresh:()=>Promise<void>; announce:(message:string,type?:Notice['type'])=>void }) {
  async function create(event:FormEvent<HTMLFormElement>) { event.preventDefault(); const form=event.currentTarget; const values=new FormData(form); try { await request('/projects',token,{method:'POST',body:JSON.stringify({customer_id:String(values.get('customer_id')),name:String(values.get('name')),notes:String(values.get('notes')||'')})}); form.reset(); await onRefresh(); announce('Proyecto creado con folio único.'); } catch(error) { announce(error instanceof Error?error.message:'No se pudo crear el proyecto.','error'); } }
  const labels={planning:'Planeación',active:'En curso',completed:'Completado'};
  return <div className="dashboard-grid"><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">CONTROL POR PROYECTO</span><h2>{items.length} proyectos</h2><p className="muted-copy">Cada proyecto tiene un folio propio para reunir órdenes, gastos y costeo.</p></div></div>{canWrite&&<form className="team-form" onSubmit={create}><h3>Nuevo proyecto</h3><label className="field"><span>Cliente</span><select name="customer_id" required defaultValue=""><option value="">Selecciona un cliente</option>{customers.map(customer=><option key={customer.id} value={customer.id}>{customer.name} · {customer.city}</option>)}</select></label><Field label="Nombre del proyecto" name="name" required minLength={2} placeholder="Sistema solar · ubicación"/><Field className="span-two" label="Notas" name="notes" placeholder="Alcance o referencias"/><button className="button button-primary">Crear proyecto</button></form>}</section><section className="surface-card table-surface"><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FOLIO</th><th>PROYECTO / CLIENTE</th><th>ÓRDENES</th><th>ESTADO</th><th>CREADO</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td><b>{item.code}</b></td><td>{item.name}<small className="sub-cell">{item.customer?.name||'Cliente'} · {item.customer?.city||'Ubicación pendiente'}</small>{item.notes&&<small className="sub-cell">{item.notes}</small>}</td><td>{item.work_orders.length?item.work_orders.map(order=>order.folio||'OT pendiente').join(', '):'Sin órdenes'}</td><td><span className={`status-chip ${item.status==='completed'?'status-approved':item.status==='active'?'status-sent':'status-draft'}`}>{labels[item.status]}</span></td><td>{new Date(item.created_at).toLocaleDateString('es-MX')}</td></tr>)}</tbody></table>{!items.length&&<EmptyState title="Sin proyectos registrados" body="Registra un proyecto aquí o crea una orden de trabajo; esa acción también prepara el proyecto automáticamente."/>}</div></section></div>;
}

function InstallationsView({ items, projects, customers, team, canWrite, token, onRefresh, announce }: { items: Installation[]; projects:Project[]; customers: Customer[]; team: TeamMember[]; canWrite: boolean; token: string; onRefresh: () => Promise<void>; announce: (message: string, type?: Notice['type']) => void }) {
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const date = String(form.get('scheduled_at') || '');
    const assignedInstallers = form.getAll('assigned_installers').map(String);
    const payload = { customer_id: String(form.get('customer_id') || ''), project_id:String(form.get('project_id')||'')||null, lead_installer: assignedInstallers[0] || '', assigned_installers: assignedInstallers, scheduled_at: date ? new Date(date).toISOString() : null, notes: String(form.get('notes') || '') };
    try { await request('/installations', token, { method: 'POST', body: JSON.stringify(payload) }); await onRefresh(); event.currentTarget.reset(); announce('Orden asignada al instalador.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo crear la orden.', 'error'); }
  }
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">COORDINACIÓN DE CAMPO</span><h2>{items.length} órdenes de trabajo</h2></div></div>{canWrite && <form className="team-form" onSubmit={create}><label className="field"><span>Cliente</span><select name="customer_id" required><option value="">Selecciona cliente</option>{customers.map(customer=><option key={customer.id} value={customer.id}>{customer.name} · {customer.city}</option>)}</select></label><label className="field"><span>Proyecto existente (opcional)</span><select name="project_id" defaultValue=""><option value="">Crear proyecto automáticamente</option>{projects.map(project=><option key={project.id} value={project.id}>{project.code} · {project.name}</option>)}</select></label><label className="field"><span>Cuadrilla instaladora</span><select name="assigned_installers" multiple required size={Math.min(5, Math.max(2, team.filter(member=>member.roles.includes('instalador')).length))}>{team.filter(member=>member.roles.includes('instalador')).map(member=><option key={member.id} value={member.email}>{member.name} · {member.email}</option>)}</select><small>Selecciona una o más cuentas instaladoras; la primera será responsable.</small></label><Field label="Fecha y hora" name="scheduled_at" type="datetime-local"/><Field label="Instrucciones" name="notes" placeholder="Alcance y detalles de la orden"/><button className="button button-primary">Asignar orden de trabajo</button></form>}{items.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROYECTO / FOLIO</th><th>CLIENTE</th><th>CONTACTO</th><th>INSTALADOR</th><th>FECHA</th><th>MATERIALES</th><th>ESTADO</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.project?.code||item.folio||'Proyecto'}<small className="sub-cell">{item.project?.name||''}</small></td><td>{item.customer?.name||'Cliente'}<small className="sub-cell">{item.customer?.city}</small></td><td>{item.customer?.phone||'—'}<small className="sub-cell">{item.customer?.email||''}</small></td><td>{(item.assigned_installers||[item.lead_installer]).join(', ')}<small className="sub-cell">{item.confirmed_installers?.length||0}/{item.assigned_installers?.length||1} confirmadas</small></td><td>{item.scheduled_at?new Date(item.scheduled_at).toLocaleString('es-MX'):'Por programar'}</td><td>{item.materials?.length ? item.materials.map(line=><div key={line.id}><b>{line.item_name}</b><small className="sub-cell">{line.shortage_quantity>0?`Faltan ${line.shortage_quantity} para completar`:`Cubierto · ${line.available_for_order ?? '—'} disponibles`}</small></div>) : 'Sin solicitud'}</td><td>{item.status}</td></tr>)}</tbody></table></div>:<EmptyState title="Sin órdenes de trabajo" body="Las asignaciones aparecerán aquí y en la PWA del instalador."/>}</section>;
}

function CatalogView({ catalog, onSave, onLogin }: { catalog: CatalogPayload | null; onSave: (event: FormEvent<HTMLFormElement>, item: Package) => Promise<boolean>; onLogin: () => void }) {
  const [editingPackage, setEditingPackage] = useState<Package | null>(null);
  const [newCount, setNewCount] = useState(4);
  const beginNewPackage = () => { if (items.some(item => item.panel_count === newCount)) { setEditingPackage(items.find(item => item.panel_count === newCount)!); return; } setEditingPackage({ id: '', panel_count: newCount, panel_brand: '', panel_watts: 0, panel_unit_price: 0, structure_name: '', structure_price: 0, inverter_options: [], default_inverter: '', payment_methods: ['Contado'], enabled: true, pricing_approved: false, price_mxn: 0, system_kw: 0 }); };
  const items = catalog?.packages || [];
  return <><div className="catalog-summary"><div><span className="eyebrow">CONFIGURACIÓN COMERCIAL</span><h2>Paquetes de 4 a 20 paneles</h2><p>{catalog?.catalog_note || 'Configura el catálogo de cotización.'}</p></div><div className="toolbar-actions"><select aria-label="Cantidad de paneles del paquete" value={newCount} onChange={event => setNewCount(Number(event.target.value))}>{Array.from({length:17},(_,i)=>i+4).map(count=><option key={count} value={count}>{count} paneles</option>)}</select><button className="button button-primary" onClick={beginNewPackage}>＋ Agregar paquete</button></div></div><section className="package-grid">{items.map(item => <article className="package-card" key={item.panel_count}><div className="package-head"><span className="package-count">{item.panel_count}<small>paneles</small></span><span className={`status-chip ${item.pricing_approved ? 'status-approved' : 'status-overdue'}`}>{item.pricing_approved ? 'Aprobado' : 'Pendiente de aprobación'}</span></div><h3>{item.panel_brand} {item.panel_watts} W</h3><p>{item.system_kw.toFixed(1)} kWp · {item.default_inverter || 'Inversor pendiente'}</p><div className="package-price">{money(item.price_mxn)}<small>{item.enabled ? 'precio de paquete' : 'desactivado'}</small></div><button className="button button-outline" onClick={() => setEditingPackage(item)}>Editar paquete</button></article>)}</section>{!items.length && <EmptyState title="No hay paquetes configurados" body="Agrega los equipos y precios vigentes aprobados por Arco Energy." action="Configurar paquete" onClick={beginNewPackage}/>}
    {editingPackage && <Modal title={`${editingPackage.panel_count} paneles`} subtitle="Edita valores y marca si están aprobados para cotizar con clientes." onClose={() => setEditingPackage(null)} wide><form className="form-grid" onSubmit={async event => { if (await onSave(event, editingPackage)) setEditingPackage(null); }}><Field label="Marca de panel" name="panel_brand" required defaultValue={editingPackage.panel_brand}/><Field label="Potencia por panel (W)" name="panel_watts" type="number" min="100" max="1000" required defaultValue={editingPackage.panel_watts}/><Field label="Precio por panel (MXN)" name="panel_unit_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.panel_unit_price}/><Field label="Nombre de estructura" name="structure_name" required defaultValue={editingPackage.structure_name}/><Field label="Precio de estructura (MXN)" name="structure_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.structure_price}/><label className="field span-two">Inversores disponibles <small>Un inversor por línea: Nombre | Precio MXN</small><textarea name="inverters" required defaultValue={editingPackage.inverter_options.map(item => `${item.name} | ${item.price_mxn}`).join('\n')}/></label><Field label="Inversor predeterminado" name="default_inverter" required defaultValue={editingPackage.default_inverter}/><div className="field"><span>Formas de pago</span><div className="check-list">{['Contado', 'Financiamiento', 'Plan 24'].map(method => <label key={method}><input type="checkbox" name="payment_method" value={method} defaultChecked={editingPackage.payment_methods.includes(method)}/>{method}</label>)}</div></div><label className="check-confirm span-two"><input type="checkbox" name="enabled" defaultChecked={editingPackage.enabled}/> Paquete disponible para nuevas cotizaciones</label><label className="approval-confirm span-two"><input type="checkbox" name="approved_prices"/> Confirmo que estos precios y equipos fueron revisados y aprobados por Arco Energy.</label><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setEditingPackage(null)}>Cancelar</button><button className="button button-primary">Guardar paquete</button></div></form></Modal>}
  </>;
}

function TeamView({ members, roleDefinitions, loading, error, name, email, password, role, busy, onName, onEmail, onPassword, onRole, onSubmit, onUpdateRole }: { members: TeamMember[]; roleDefinitions: RoleDefinition[]; loading: boolean; error: string; name: string; email: string; password: string; role: string; busy: boolean; onName: (v: string) => void; onEmail: (v: string) => void; onPassword: (v: string) => void; onRole: (v: string) => void; onSubmit: (e: FormEvent<HTMLFormElement>) => void; onUpdateRole: (id: string, role: string) => void }) {
  return <><section className="surface-card team-surface"><div className="section-title"><div><span className="eyebrow">CUENTAS Y PERMISOS</span><h2>Personas en el equipo</h2></div><span className="status-chip status-approved">5 roles</span></div><p className="muted-copy">Los permisos se validan en la API además de controlar qué se muestra en cada pantalla.</p><form className="team-form" onSubmit={onSubmit}><Field label="Nombre" value={name} onChange={onName} required placeholder="Nombre completo"/><Field label="Correo" type="email" value={email} onChange={onEmail} required placeholder="persona@arcoenergy.mx"/><Field label="Contraseña inicial" type="password" value={password} onChange={onPassword} required minLength={12} placeholder="12 caracteres mínimo"/><label className="field"><span>Rol</span><select value={role} onChange={event => onRole(event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{role === 'cliente' && <p className="muted-copy span-two">Primero registra al cliente en la cartera con este mismo correo. El acceso del portal se asocia a esa ficha y muestra solo sus propuestas, instalaciones y pagos.</p>}<button className="button button-primary" disabled={busy}>{busy ? 'Creando…' : '＋ Crear usuario'}</button></form>{error && <p className="error-message">{error}</p>}{loading && <p className="muted-copy">Cargando equipo y permisos…</p>}<div className="team-list">{members.map(member => <div className="team-row" key={member.id}><span className="avatar-soft">{initials(member.name)}</span><div><b>{member.name}</b><small>{member.email}</small></div><select aria-label={`Rol de ${member.name}`} value={member.roles[0] || ''} onChange={event => onUpdateRole(member.id, event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>)}</div></section><section className="surface-card role-matrix"><div className="section-title"><div><span className="eyebrow">MATRIZ DE ACCESO</span><h2>Qué puede hacer cada rol</h2></div></div><p className="muted-copy">Permisos configurados en la API. Son asignaciones predefinidas; el CRM no permite añadir permisos individuales.</p>{roleDefinitions.length ? <div className="role-matrix-grid">{roleDefinitions.map(definition => <article className="role-permission-card" key={definition.id}><h3>{definition.label}</h3><ul>{definition.permissions.map(permission => <li key={permission}>{permissionLabel[permission] || permission}</li>)}</ul></article>)}</div> : <p className="muted-copy">{loading ? 'Cargando matriz…' : 'No fue posible cargar la matriz de permisos.'}</p>}</section></>;
}

function QuoteComposer({ packages, customers, onClose, onSubmit, onNewCustomer }: { packages: Package[]; customers: Customer[]; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onNewCustomer: () => void }) {
  const [count, setCount] = useState(packages.find(item => item.enabled)?.panel_count || 4);
  const [customerId, setCustomerId] = useState(customers[0]?.id || '');
  const selected = packages.find(item => item.panel_count === count);
  const selectedCustomer = customers.find(item => item.id === customerId);
  const [inverter, setInverter] = useState('');
  useEffect(() => setInverter(selected?.default_inverter || ''), [selected]);
  if (!selected) return <Modal title="Catálogo pendiente" subtitle="No hay paquetes activos disponibles." onClose={onClose}><EmptyState title="Configura el catálogo" body="Un administrador debe habilitar paquetes antes de cotizar."/></Modal>;
  const price = selected.panel_unit_price * count + selected.structure_price + (selected.inverter_options.find(item => item.name === (inverter || selected.default_inverter))?.price_mxn || 0);
  return <Modal title="Nueva cotización" subtitle="Selecciona cliente, sistema y forma de pago." onClose={onClose} wide><form className="form-grid" onSubmit={onSubmit}><label className="field span-two"><span>Cliente</span><select name="customer_id" value={customerId} onChange={event => setCustomerId(event.target.value)} required><option value="">Selecciona un cliente</option>{customers.map(item => <option key={item.id} value={item.id}>{item.name} · {item.city}</option>)}</select>{!customers.length && <button type="button" className="text-button" onClick={onNewCustomer}>＋ Agregar cliente</button>}</label><label className="field"><span>Cantidad de paneles</span><select name="panel_count" value={count} onChange={event => setCount(Number(event.target.value))}>{packages.filter(item => item.enabled).map(item => <option key={item.panel_count} value={item.panel_count}>{item.panel_count} paneles · {item.system_kw.toFixed(1)} kWp</option>)}</select></label><label className="field"><span>Inversor</span><select name="inverter" value={inverter || selected.default_inverter} onChange={event => setInverter(event.target.value)}>{selected.inverter_options.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label><label className="field"><span>Marca / potencia</span><div className="readonly-field">{selected.panel_brand} · {selected.panel_watts} W</div></label><label className="field"><span>Forma de pago</span><select name="payment_method">{selected.payment_methods.map(method => <option key={method}>{method}</option>)}</select></label><Field className="span-two" label="Domicilio de instalación" name="installation_address" defaultValue={selectedCustomer?.address || ''} placeholder="Calle, colonia y referencias"/><Field label="Ciudad" name="installation_city" defaultValue={selectedCustomer?.city || ''} required placeholder="Tampico"/><div className="quote-total span-two"><div><small>INVERSIÓN ESTIMADA {!selected.pricing_approved && <b>· PRECIO PENDIENTE DE APROBACIÓN</b>}</small><strong>{money(price)}</strong><span>{count} × {money(selected.panel_unit_price)} panel · {selected.structure_name} · {inverter}</span></div><span>{(count * selected.panel_watts / 1000).toFixed(2)} kWp</span></div>{!selected.pricing_approved && <div className="inline-disclaimer span-two">Completa la revisión y aprobación del paquete antes de emitir una propuesta comercial.</div>}<div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={onClose}>Cancelar</button><button className="button button-primary" disabled={!selected.pricing_approved}>Guardar y descargar PDF</button></div></form></Modal>;
}

function CustomerDrawer({ customer, quotes, followups, activities, canWrite, canAssign, team, currentEmail, onClose, onAddActivity, onSchedule, onDownload }: { customer: Customer; quotes: Quote[]; followups: FollowUp[]; activities: Activity[]; canWrite: boolean; canAssign: boolean; team: TeamMember[]; currentEmail: string; onClose: () => void; onAddActivity: (event: FormEvent<HTMLFormElement>) => void; onSchedule: (event: FormEvent<HTMLFormElement>) => void; onDownload: (quote: Quote) => void }) {
  const [mode, setMode] = useState<'nota' | 'seguimiento'>('nota');
  const defaultDate = addLocalCalendarDays(new Date(), 3);
  const [followupDays, setFollowupDays] = useState('3');
  const [followupDate, setFollowupDate] = useState(defaultDate);
  function selectFollowup(value: string) { setFollowupDays(value); if (value !== 'custom') setFollowupDate(addLocalCalendarDays(new Date(), Number(value))); }
  return <div className="drawer-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><aside className="customer-drawer"><header><div><span className="eyebrow">FICHA DE CLIENTE</span><button className="drawer-close" onClick={onClose}>×</button></div><div className="drawer-profile"><span className="profile-avatar">{initials(customer.name)}</span><div><h2>{customer.name}</h2><small>{customer.city} · {labelCustomerStatus(customer.status)}</small></div></div><div className="contact-actions"><a href={customer.phone ? `tel:${customer.phone}` : undefined} aria-disabled={!customer.phone}>☎ Llamar</a><a className="wa-action" target="_blank" rel="noreferrer" href={customer.phone ? `https://wa.me/${customer.phone.replace(/\D/g, '')}` : undefined}>◉ WhatsApp</a></div><div className="contact-block"><b>Datos de contacto</b><span>{customer.phone || 'Teléfono pendiente'}</span><span>{customer.email || 'Correo pendiente'}</span><span>{customer.address || customer.city || 'Ubicación pendiente'}</span></div></header><div className="drawer-body"><section><div className="section-title"><div><span className="eyebrow">PROPUESTAS</span><h3>{quotes.length} cotizaciones</h3></div></div>{quotes.length ? quotes.map(item => <div className="drawer-quote" key={item.id}><div><b>{item.folio}</b><small>{item.panel_count} paneles · {item.status}</small></div><strong>{money(item.total)}</strong><button className="icon-button" onClick={() => onDownload(item)}>PDF</button></div>) : <p className="empty-inline">Sin cotizaciones todavía.</p>}</section><section><div className="section-title"><div><span className="eyebrow">PRÓXIMO CONTACTO</span><h3>{followups.length} seguimientos</h3></div></div>{followups.map(item => <div className="drawer-followup" key={item.id}><b>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}</b><span>{item.note}</span><small>Responsable: {item.assigned_to || 'pendiente'}</small></div>)}</section>{canWrite && <section className="note-box"><div className="note-tabs"><button className={mode === 'nota' ? 'active' : ''} onClick={() => setMode('nota')}>Agregar nota</button><button className={mode === 'seguimiento' ? 'active' : ''} onClick={() => setMode('seguimiento')}>Programar seguimiento</button></div>{mode === 'nota' ? <form onSubmit={onAddActivity}><textarea name="note" required maxLength={5000} placeholder="Escribe una nota para la bitácora…"/><button className="button button-primary">Guardar nota</button></form> : <form onSubmit={onSchedule}><label className="field"><span>Cuándo volver a contactar</span><select value={followupDays} onChange={event => selectFollowup(event.target.value)}><option value="3">En 3 días</option><option value="7">En 7 días</option><option value="15">En 15 días</option><option value="30">En 30 días</option><option value="custom">Elegir fecha</option></select></label><label className="field"><span>Fecha para contactar</span><input name="due_date" type="date" min={localDateInputValue()} value={followupDate} onChange={event => { setFollowupDate(event.target.value); setFollowupDays("custom"); }} required/></label><label className="field"><span>Motivo / comentario del cliente</span><textarea name="note" required placeholder="¿Qué comentó y qué hay que retomar?"/></label>{canAssign && <label className="field"><span>Persona responsable</span><select name="assigned_to" defaultValue={currentEmail.toLowerCase()} required><option value={currentEmail.toLowerCase()}>Yo · {currentEmail}</option>{team.filter(member => member.email.toLowerCase() !== currentEmail.toLowerCase()).map(member => <option key={member.id} value={member.email.toLowerCase()}>{member.name} · {member.email}</option>)}</select></label>}<button className="button button-primary">Programar contacto</button></form>}</section>}<section><div className="section-title"><div><span className="eyebrow">BITÁCORA</span><h3>Actividad reciente</h3></div></div>{activities.length ? activities.map(item => <div className="activity-row" key={item.id}><i/><div><b>{item.kind}</b><p>{item.note}</p><small>{item.created_by || 'Equipo'} · {new Date(item.created_at).toLocaleString('es-MX')}</small></div></div>) : <p className="empty-inline">Aún no hay actividad registrada.</p>}</section></div><footer className="drawer-foot">{`Origen: ${customer.source === 'public_web' ? 'Web pública' : 'Equipo Arco Energy'}`}</footer></aside></div>;
}

function Metric({ label, value, note, icon, tone }: { label: string; value: string; note: string; icon: string; tone: string }) { return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className={`metric-icon tone-${tone}`}>{icon}</i></div><strong>{value}</strong><small>{note}</small></article>; }
function EmptyState({ title, body, action, onClick }: { title: string; body: string; action?: string; onClick?: () => void }) { return <div className="empty-state"><span>✦</span><h3>{title}</h3><p>{body}</p>{action && onClick && <button className="button button-outline" onClick={onClick}>{action}</button>}</div>; }
function Modal({ title, subtitle, onClose, wide = false, children }: { title: string; subtitle: string; onClose: () => void; wide?: boolean; children: ReactNode }) { return <div className="modal-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className={`modal-card ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><header className="modal-header"><div><span className="eyebrow">ARCO ENERGY</span><h2>{title}</h2><p>{subtitle}</p></div><button className="drawer-close" onClick={onClose} aria-label="Cerrar">×</button></header><div className="modal-body">{children}</div></section></div>; }
function Field({ label, name, type = 'text', required = false, placeholder, defaultValue, value, onChange, className = '', min, max, step, minLength, maxLength }: { label: string; name?: string; type?: string; required?: boolean; placeholder?: string; defaultValue?: string | number; value?: string; onChange?: (value: string) => void; className?: string; min?: string | number; max?: string | number; step?: string | number; minLength?: number; maxLength?: number }) { return <label className={`field ${className}`}><span>{label}</span><input name={name} type={type} required={required} placeholder={placeholder} defaultValue={value === undefined ? defaultValue : undefined} value={value} onChange={event => onChange?.(event.target.value)} min={min} max={max} step={step} minLength={minLength} maxLength={maxLength}/></label>; }
function labelStatus(status: string) { return ({ draft: 'Borrador', sent: 'Enviada', accepted: 'Aceptada', declined: 'No aceptada', overdue: 'Vencido' })[status] || status; }
function labelCustomerStatus(status: string) { return ({ lead: 'Prospecto', qualified: 'En conversación', followup: 'Seguimiento', customer: 'Cliente' })[status] || status; }
function LoginScreen() { const { login, loading, error } = useAuth(); const [failure, setFailure] = useState(''); return <div className="login-screen"><a className="crm-brand" href="/"><span className="brand-mark">A</span><span>arco<span>energy</span><small>GESTIÓN SOLAR</small></span></a><section className="login-card"><span className="eyebrow">ACCESO DE EQUIPO</span><h1>Iniciar sesión</h1><p>Ingresa con la cuenta de tu negocio.</p><form onSubmit={async event => { event.preventDefault(); const form = new FormData(event.currentTarget); setFailure(''); try { await login(String(form.get('email')), String(form.get('password')), form.get('remember') === 'on'); window.location.replace('/crm/'); } catch (err) { setFailure(err instanceof Error ? err.message : error || 'No se pudo iniciar sesión.'); } }}><Field label="Correo electrónico" name="email" type="email" required/><Field label="Contraseña" name="password" type="password" required/><label className="field"><span><input type="checkbox" name="remember" defaultChecked/> Mantener sesión iniciada</span></label>{failure && <p role="alert">{failure}</p>}<button className="button button-primary" disabled={loading}>{loading ? 'Iniciando…' : 'Entrar'}</button></form><a href="/app/login">Acceso móvil</a></section></div>; }
