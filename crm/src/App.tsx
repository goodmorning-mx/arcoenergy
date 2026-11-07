import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react';
import { AgentChat } from '@goodmorning/gm-agent';
import { useAuth } from '@goodmorning/gm-auth';
import { QRCodeSVG } from 'qrcode.react';
import { OperationsReportView } from './OperationsReportView';
import { InventoryIssueIntake } from './InventoryIssueIntake';
import './inventory-labels.css';

type View = 'inicio' | 'clientes' | 'cotizaciones' | 'ventas' | 'seguimientos' | 'instalaciones' | 'inventario' | 'gastos' | 'cobranza' | 'cuentas' | 'proveedores' | 'compras' | 'reportes' | 'catalogo' | 'equipo' | 'historial';
type Customer = { id: string; name: string; phone: string; email: string; city: string; address: string; status: string; source: string; created_at?: string };
type Quote = { id: string; folio: string; customer_id: string; customer?: Customer; panel_count: number; panel_brand: string; panel_watts: number; inverter: string; payment_method: string; total: number; status: string; pricing_approved: boolean; installation_city: string; installation_address: string; created_at: string };
type Package = { id: string; panel_count: number; panel_brand: string; panel_watts: number; panel_unit_price: number; structure_name: string; structure_price: number; inverter_options: Array<{ name: string; price_mxn: number }>; default_inverter: string; payment_methods: string[]; enabled: boolean; pricing_approved: boolean; price_mxn: number; system_kw: number };
type FollowUp = { id: string; customer_id: string; due_date: string; note: string; done: boolean; assigned_to: string; customer?: Customer };
type Activity = { id: string; kind: string; note: string; created_by: string; created_at: string };
type TeamMember = { id: string; name: string; email: string; roles: string[]; permissions: string[] };
type RoleDefinition = { id: string; label: string; permissions: string[] };
type Installation = { id: string; folio?: string | null; scheduled_at: string | null; lead_installer: string; assigned_installers?: string[]; confirmed_installers?: string[]; status: string; notes: string; customer?: Customer; quote_id?: string | null; materials?: Array<{ id: string; item_id: string; item_name: string; requested_quantity: number; preissued_quantity: number; consumed_quantity: number; remaining_quantity: number; remaining_to_issue: number }> };
type InventoryItem = { id: string; name: string; description?: string; category?: string; brand?: string; model?: string; supplier_id?: string | null; barcode?: string | null; unit: string; quantity: number; reserved_quantity?: number; available_quantity?: number; minimum_quantity: number; unit_cost: number };
type InventoryMovement = { id: string; item_id: string; item_name: string; unit: string; quantity: number; signed_quantity: number; movement_type: string; unit_cost?: number | null; reason: string; created_by: string; created_at: string; installation_id?: string | null; returnable_quantity?: number };
type ProjectExpense = { id: string; installation_id: string | null; account_id: string | null; account_name: string | null; category: string; description: string; amount: number; receipt_url: string; occurred_on: string; created_by: string; project_customer: string; project_city: string };
type FinancialAccount = { id: string; name: string; account_type: 'cash' | 'bank'; opening_balance: number; opening_balance_date: string; current_balance: number; movement_count: number };
type CashMovement = { id: string; account_id: string; direction: 'in' | 'out'; amount: number; category: string; description: string; occurred_on: string; source_type: string; source_id: string | null; reversal_of_id: string | null; created_by: string };
type Supplier = { id: string; name: string; rfc: string; phone: string; email: string; payment_terms: 'cash' | 'credit'; credit_days: number; active: boolean; current_balance: number };
type Purchase = { id: string; folio: string; supplier_id: string; supplier?: { id: string; name: string }; invoice_number: string; payment_terms: 'cash' | 'credit'; purchase_date: string; due_date: string | null; total: number; paid_amount: number; balance: number; status: string; payments?: Array<{ id: string; amount: number; paid_on: string; reference: string; is_reversal: boolean; can_reverse: boolean }>; lines: Array<{ id: string; item_name: string; quantity: number; unit_cost: number; line_total: number }> };
type CfdiProposal = { invoice_reference:string; purchase_date:string; supplier_rfc:string; supplier_name:string; declared_subtotal:number; global_discount:number; declared_total:number; requires_accounting_review:boolean; concepts:Array<{identifier:string;product_service_key:string;description:string;quantity:number;unit:string;net_line_amount:number;unit_cost_before_global_adjustments:number}> };
type Receivable = { id: string; customer_id: string; customer?: Customer; quote_id: string | null; due_date: string; amount: number; paid_amount: number; balance: number; installment_number: number; payment_method: string; status: 'pending' | 'partial' | 'overdue' | 'paid'; payments?: Array<{ id: string; amount: number; paid_on: string; reference: string; account_name: string; is_reversal: boolean; can_reverse: boolean }> };
type Installer = { email: string; name: string };
type Sale = { id: string; folio: string; customer_id: string; customer?: Customer; quote_id: string; quote?: { id: string; folio: string; payment_method: string }; installation_id: string; installation?: Installation; sale_type: 'cash' | 'credit'; total: number; receivable?: { due_date: string; amount: number; paid_amount: number } | null; materials: Array<{ id: string; item_name: string; quantity: number }>; created_at: string };
type Dashboard = { customers?: number; quotes_open?: number; quotes_amount?: number; installations_active?: number; receivables_open?: number; due_receivables?: Array<{id:string;customer:string;due_date:string;balance:number;status:'due'|'overdue'}>; low_stock_items?: Array<{id:string;name:string;unit:string;available_quantity:number;minimum_quantity:number}>; account_balances?: Array<{id:string;name:string;account_type:string;balance:number}> };
type CatalogPayload = { packages: Package[]; payment_methods: string[]; catalog_note: string };
type ProfitabilityRow = { installation_id: string | null; folio: string | null; project: string; city: string; sales: number; materials_cost: number | null; expenses: number; expenses_by_category: Record<string, number>; preliminary_result: number | null; missing_cost_movements: number; material_events: number };
type ProfitabilityReport = { period: string; basis: string; rows: ProfitabilityRow[]; totals: { sales: number; materials_cost: number | null; expenses: number; preliminary_result: number | null; missing_cost_movements: number }; returns_and_bonifications: { recorded: boolean; included: boolean }; complete_financial_statement: boolean };
type Notice = { type: 'success' | 'error' | 'info'; text: string };

const apiBase = '/api/v1';
const money = (amount: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 2 }).format(amount || 0);
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
  const [catalog, setCatalog] = useState<CatalogPayload | null>(null);
  const [search, setSearch] = useState('');
  const [customerOpen, setCustomerOpen] = useState(false);
  const [quoteOpen, setQuoteOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [agentOpen, setAgentOpen] = useState(false);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [roleDefinitions, setRoleDefinitions] = useState<RoleDefinition[]>([]);
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [inventoryMovements, setInventoryMovements] = useState<InventoryMovement[]>([]);
  const [expenses, setExpenses] = useState<ProjectExpense[]>([]);
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
    ...(can('installations:read') ? ['instalaciones' as View] : []),
    ...(can('inventory:read') ? ['inventario' as View] : []),
    ...(can('expenses:read') ? ['gastos' as View] : []),
    ...(can('receivables:read') ? ['cobranza' as View] : []),
    ...(can('accounts:read') ? ['cuentas' as View] : []),
    ...(can('suppliers:read') ? ['proveedores' as View] : []),
    ...(can('purchases:read') ? ['compras' as View] : []),
    ...(can('reports:read') ? ['reportes' as View] : []),
    ...(can('team:manage') ? ['catalogo' as View, 'equipo' as View, 'historial' as View] : []),
  ]), [can, clientAccount]);
  const title: Record<View, string> = { inicio: 'Resumen', clientes: 'Clientes', cotizaciones: 'Cotizaciones', ventas: 'Ventas y órdenes', seguimientos: 'Seguimientos', instalaciones: 'Instalaciones', inventario: 'Inventario', gastos: 'Gastos operativos', cobranza: 'Cuentas por cobrar', cuentas: 'Caja y bancos', proveedores: 'Proveedores', compras: 'Compras y cuentas por pagar', reportes: 'Costeo por proyecto', catalogo: 'Catálogo de paquetes', equipo: 'Equipo y accesos', historial: 'History cards' };

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

  useEffect(() => { const timer = window.setTimeout(() => setAuthResolved(true), 0); return () => window.clearTimeout(timer); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (allowedViews.length && !allowedViews.includes(view)) setView(allowedViews[0]); }, [allowedViews, view]);

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
    const payload = { installation_id: String(data.get('installation_id') || '') || null, account_id: String(data.get('account_id') || '') || null, category: String(data.get('category') || 'Otro'), description: String(data.get('description') || '').trim(), amount: Number(data.get('amount')), occurred_on: String(data.get('occurred_on')), receipt_url: String(data.get('receipt_url') || '').trim() };
    try { const created = await request<ProjectExpense>('/expenses', accessToken, { method: 'POST', body: JSON.stringify(payload) }); setExpenses(rows => [created, ...rows]); form.reset(); if (can('accounts:read')) setAccounts(await request<FinancialAccount[]>('/accounts', accessToken)); announce('Gasto registrado y vinculado a su cuenta de caja o banco.'); }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar el gasto.', 'error'); }
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

  async function reverseCashMovement(movement: CashMovement) {
    if (!accessToken) return;
    try { await request<CashMovement>(`/cash-movements/${movement.id}/reverse`, accessToken, { method: 'POST' }); const [rows, report] = await Promise.all([request<FinancialAccount[]>('/accounts', accessToken), request<{ movements: CashMovement[] }>(`/accounts/${selectedAccountId}/movements`, accessToken)]); setAccounts(rows); setAccountMovements(report.movements); announce('Corrección registrada como reversa; se conservó el movimiento original.'); }
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
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo descargar el PDF.', 'error'); }
  }

  async function shareQuote(quote: Quote) {
    if (!quote.pricing_approved) { announce('Aprueba el precio del paquete antes de compartir la propuesta.', 'error'); return; }
    const phone = quote.customer?.phone?.replace(/\D/g, '') || '';
    const message = `Hola ${quote.customer?.name || ''}, te comparto la propuesta ${quote.folio} de Arco Energy por ${money(quote.total)}. Adjunto el PDF en esta conversación.`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank', 'noopener,noreferrer');
    announce('WhatsApp abrió la conversación. Adjunta el PDF descargado antes de enviarlo.', 'info');
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
  if (['/login', '/crm/login'].includes(window.location.pathname.replace(/\/$/, ''))) { if (identity) { window.location.replace(clientAccount ? '/app/' : '/crm/'); return null; } return <LoginScreen />; }
  if (!identity || !accessToken) { window.location.replace('/crm/login'); return null; }
  if (clientAccount) { window.location.replace('/app/'); return null; }

  const nav: Array<[View, string, string]> = [['inicio', '◫', 'Resumen'], ['clientes', '♙', 'Clientes'], ['cotizaciones', '▤', 'Cotizaciones'], ...(can('sales:read') ? [['ventas', '▣', 'Ventas / OT']] as Array<[View, string, string]> : []), ['seguimientos', '◷', 'Seguimientos'], ...(can('installations:read') ? [['instalaciones', '⌂', 'Instalaciones']] as Array<[View, string, string]> : []), ...(can('inventory:read') ? [['inventario', '▦', 'Inventario']] as Array<[View, string, string]> : []), ...(can('expenses:read') ? [['gastos', '$', 'Gastos']] as Array<[View, string, string]> : []), ...(can('receivables:read') ? [['cobranza', '↙', 'Cobranza']] as Array<[View, string, string]> : []), ...(can('accounts:read') ? [['cuentas', '▤', 'Caja / bancos']] as Array<[View, string, string]> : []), ...(can('suppliers:read') ? [['proveedores', '♧', 'Proveedores']] as Array<[View, string, string]> : []), ...(can('purchases:read') ? [['compras', '▤', 'Compras / CxP']] as Array<[View, string, string]> : []), ...(can('reports:read') ? [['reportes', '▥', 'Reportes']] as Array<[View, string, string]> : []), ...(can('team:manage') ? [['catalogo', '⊞', 'Catálogo'], ['equipo', '♧', 'Equipo'], ['historial', '↺', 'History cards']] as Array<[View, string, string]> : [])];
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
        {view === 'cotizaciones' && <QuotesView quotes={quotes} onCreate={() => setQuoteOpen(true)} onDownload={downloadQuote} onShare={shareQuote} onMarkSent={markQuoteSent} onAccept={acceptQuote} canWrite={can('quotes:write')} />}
        {view === 'ventas' && <SalesView items={sales} quotes={quotes} inventory={inventory} installers={installers} accounts={accounts} canWrite={can('sales:write')} token={accessToken || ''} onItems={setSales} onAccounts={setAccounts} onInventory={setInventory} onRefresh={refresh} announce={announce} />}
        {view === 'seguimientos' && <FollowupsView items={followups} onComplete={completeFollowup} onCustomer={setSelectedCustomer} />}
        {view === 'instalaciones' && <InstallationsView items={installations} customers={customers} team={team} canWrite={can('installations:write')} token={accessToken || ''} onRefresh={refresh} announce={announce} />}
        {view === 'inventario' && <InventoryView items={inventory} movements={inventoryMovements} installations={installations} suppliers={suppliers} canManage={can('inventory:manage')} canIssue={can('inventory:issue')} canReadCosts={can('inventory:costs:read') || can('inventory:manage')} token={accessToken || ''} onRefresh={refresh} onMovements={setInventoryMovements} onInstallations={setInstallations} announce={announce} />}
        {view === 'gastos' && <ExpensesView items={expenses} installations={installations} accounts={accounts} canWrite={can('expenses:write')} onSubmit={createExpense} />}
        {view === 'cobranza' && <ReceivablesView items={receivables} customers={customers} quotes={quotes} accounts={accounts} canWrite={can('receivables:write')} token={accessToken || ''} onCreate={createReceivable} onItems={setReceivables} onAccounts={setAccounts} announce={announce} />}
        {view === 'cuentas' && <AccountsView accounts={accounts} selectedId={selectedAccountId} onSelect={setSelectedAccountId} movements={accountMovements} canManage={can('accounts:manage')} canWrite={can('accounts:write')} onCreateAccount={createAccount} onCreateMovement={createCashMovement} onReverse={reverseCashMovement} />}
        {view === 'proveedores' && <SuppliersView items={suppliers} canWrite={can('suppliers:manage')} onSubmit={createSupplier} />}
        {view === 'compras' && <PurchasesView items={purchases} suppliers={suppliers} inventory={inventory} accounts={accounts} canWrite={can('purchases:write')} token={accessToken || ''} onItems={setPurchases} onSuppliers={setSuppliers} onAccounts={setAccounts} onInventory={setInventory} announce={announce} />}
        {view === 'reportes' && <><OperationsReportView token={accessToken || ''} /><ProfitabilityView token={accessToken || ''} /></>}
        {view === 'catalogo' && <CatalogView catalog={catalog} onSave={savePackage} onLogin={() => window.location.assign('/crm/login')} />}
        {view === 'equipo' && <TeamView members={team} roleDefinitions={roleDefinitions} loading={teamLoading} error={teamError} name={teamName} email={teamEmail} password={teamPassword} role={teamRole} busy={teamBusy} onName={setTeamName} onEmail={setTeamEmail} onPassword={setTeamPassword} onRole={setTeamRole} onSubmit={createMember} onUpdateRole={updateMemberRole} />}
        {view === 'historial' && <HistoryCardsView token={accessToken || ''} announce={announce} />}

        <footer className="page-foot"><span>Arco Energy · CRM</span><span>La información se actualiza desde el espacio de trabajo de Arco Energy.</span></footer>
      </div>
    </main>

    <button className={`agent-launcher ${agentOpen ? 'open' : ''}`} onClick={() => setAgentOpen(value => !value)} aria-label={agentOpen ? 'Cerrar asistente' : 'Abrir asistente'}>{agentOpen ? '×' : '✦'}</button>
    {agentOpen && <aside className="agent-panel"><div className="agent-panel-head"><div><span className="agent-spark">✦</span><div><b>Asistente Arco</b><small>Consulta clientes y paquetes autorizados</small></div></div><button onClick={() => setAgentOpen(false)} aria-label="Cerrar asistente">×</button></div><AgentChat title="¿Qué necesitas resolver?" client={async (prompt, conversationId) => request<{ conversationId: string; content: string }>(accessToken ? '/agent/chat' : '/public/agent/chat', accessToken || undefined, { method: 'POST', body: JSON.stringify({ prompt, conversation_id: conversationId }) })} initialMessages={[{ role: 'assistant', content: 'Puedo consultar resúmenes y paquetes comerciales aprobados.' }]} /><div className="agent-safety">El asistente consulta datos autorizados. No crea ni modifica registros.</div></aside>}

    {customerOpen && <Modal title="Agregar cliente" subtitle="Guarda los datos de contacto y ubicación del prospecto." onClose={() => setCustomerOpen(false)}><form className="form-grid" onSubmit={createCustomer}><Field label="Nombre completo" name="name" required placeholder="Ej. Andrea García"/><Field label="Teléfono / WhatsApp" name="phone" placeholder="833 000 0000"/><Field label="Correo" name="email" type="email" placeholder="nombre@empresa.com"/><Field label="Ciudad" name="city" required placeholder="Tampico"/><Field label="Domicilio de instalación" name="address" className="span-two" placeholder="Calle, colonia y referencias"/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setCustomerOpen(false)}>Cancelar</button><button className="button button-primary">Guardar cliente</button></div></form></Modal>}
    {quoteOpen && <QuoteComposer packages={catalog?.packages.filter(item => item.enabled) || []} customers={customers} onClose={() => setQuoteOpen(false)} onSubmit={createQuote} onNewCustomer={() => { setQuoteOpen(false); setCustomerOpen(true); }} />}
    {selectedCustomer && <CustomerDrawer customer={selectedCustomer} quotes={quotes.filter(item => item.customer_id === selectedCustomer.id)} followups={followups.filter(item => item.customer_id === selectedCustomer.id)} activities={activities} canWrite={can('customers:write')} canAssign={can('team:manage')} team={team.filter(member => member.permissions.includes('customers:write'))} currentEmail={identity?.email || ''} onClose={() => setSelectedCustomer(null)} onAddActivity={addActivity} onSchedule={scheduleFollowup} onDownload={downloadQuote} />}
    {notice && <div className={`toast toast-${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}>{notice.type === 'success' ? '✓' : notice.type === 'error' ? '!' : 'ⓘ'} &nbsp;{notice.text}</div>}
    {printQuote && <div className="print-layer"><div className="print-document"><header><b>arco<span>energy</span></b><span>{printQuote.folio}</span></header><h1>Propuesta de sistema solar</h1><p>Cliente: {printQuote.customer?.name || 'Cliente'}</p><p>Instalación: {printQuote.installation_address}, {printQuote.installation_city}</p><div className="print-summary"><b>{printQuote.panel_count} paneles {printQuote.panel_brand} · {printQuote.panel_watts} W</b><span>Inversor: {printQuote.inverter}</span><span>Forma de pago: {printQuote.payment_method}</span><strong>Inversión estimada: {money(printQuote.total)}</strong></div>{!printQuote.pricing_approved && <p className="print-disclaimer">Paquete pendiente de aprobación comercial.</p>}<button className="button button-primary no-print" onClick={() => window.print()}>Imprimir / Guardar como PDF</button><button className="text-button no-print" onClick={() => setPrintQuote(null)}>Cerrar</button></div></div>}
  </div>;
}

function headingDescription(view: View) { return ({ inicio: '', clientes: 'Consulta prospectos, contactos y actividad comercial.', cotizaciones: 'Prepara, descarga y comparte propuestas con folio.', ventas: 'Registra ventas aceptadas, entradas de dinero y órdenes de trabajo.', seguimientos: 'Da continuidad a las conversaciones y registra cada contacto.', instalaciones: 'Asigna y consulta órdenes de trabajo.', inventario: 'Administra materiales, entradas y existencias.', gastos: 'Registra gastos operativos y directos por fecha y proyecto.', cobranza: 'Administra saldos, abonos recibidos y recordatorios a clientes.', cuentas: 'Consulta saldos y registra movimientos de caja y bancos.', proveedores: 'Administra proveedores y sus condiciones de pago.', compras: 'Registra entradas de material, facturas y saldos por pagar.', reportes: 'Consulta ventas, consumo de materiales y gastos por periodo o proyecto.', catalogo: 'Administra paquetes, inversores, precios y formas de pago.', equipo: 'Usuarios y privilegios para cada área.', historial: 'Conserva relatos, fuentes y versiones de cada user story card.' })[view] || ''; }

function DashboardView({ data, customers, quotes, followups, can, onCustomer, onView, onComplete }: { data: Dashboard; customers: Customer[]; quotes: Quote[]; followups: FollowUp[]; can: (p: string) => boolean; onCustomer: (c: Customer) => void; onView: (v: View) => void; onComplete: (f: FollowUp) => void }) {
  const recent = [...quotes].slice(0, 4);
  const lowStock = data.low_stock_items || [];
  const due = data.due_receivables || [];
  const balances = data.account_balances || [];
  return <>
    <section className="metric-grid">
      {can('customers:read') && <Metric label="PROSPECTOS Y CLIENTES" value={String(data.customers ?? customers.length)} note="Registros en tu cartera" icon="♙" tone="sage"/>}
      {can('quotes:read') && <Metric label="COTIZACIONES ABIERTAS" value={String(data.quotes_open ?? quotes.filter(item => item.status === 'draft' || item.status === 'sent').length)} note={`${money(data.quotes_amount ?? quotes.filter(item => item.status === 'draft' || item.status === 'sent').reduce((sum, item) => sum + item.total, 0))} en propuestas`} icon="▤" tone="blue"/>}
      {can('customers:read') && <Metric label="SEGUIMIENTOS PENDIENTES" value={String(followups.length)} note="Próximos y vencidos" icon="◷" tone="amber"/>}
      {can('installations:read') && <Metric label="INSTALACIONES ACTIVAS" value={String(data.installations_active ?? 0)} note="Visibles para tu rol" icon="⌂" tone="mint"/>}
      {can('receivables:read') && <Metric label="CARTERA POR COBRAR" value={money(data.receivables_open ?? 0)} note="Saldo pendiente registrado" icon="$" tone="rose"/>}
    </section>
    {(can('inventory:read') || can('receivables:read') || can('accounts:read')) && <section className="dashboard-grid">
      {can('inventory:read') && <div className="surface-card"><div className="section-title"><div><span className="eyebrow">ALMACÉN</span><h2>Alertas de existencias</h2></div><button className="text-button" onClick={() => onView('inventario')}>Abrir almacén →</button></div>{lowStock.length ? lowStock.map(item=><div className="focus-row" key={item.id}><div className="avatar-soft">▦</div><div><b>{item.name}</b><small>{item.available_quantity} {item.unit} disponibles · mínimo {item.minimum_quantity}</small></div><span className="status-chip status-overdue">Reponer</span></div>) : <p className="empty-inline">No hay artículos bajo el mínimo configurado.</p>}</div>}
      {can('receivables:read') && <div className="surface-card"><div className="section-title"><div><span className="eyebrow">COBRANZA</span><h2>Vencidos y próximos</h2></div><button className="text-button" onClick={() => onView('cobranza')}>Ver cartera →</button></div>{due.length ? due.map(item=><div className="focus-row" key={item.id}><div className="date-tile"><b>{new Date(`${item.due_date}T12:00:00`).getDate()}</b><small>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX',{month:'short'}).toUpperCase()}</small></div><div><b>{item.customer}</b><small>{item.status==='overdue'?'Vencido':'Vence pronto'} · {money(item.balance)}</small></div><span className={`status-chip ${item.status==='overdue'?'status-overdue':'status-draft'}`}>{item.status==='overdue'?'Vencido':'Próximo'}</span></div>) : <p className="empty-inline">Sin pagos vencidos ni próximos en los siguientes 7 días.</p>}</div>}
      {can('accounts:read') && <div className="surface-card"><div className="section-title"><div><span className="eyebrow">CAJA Y BANCOS</span><h2>Saldos actuales</h2></div><button className="text-button" onClick={() => onView('cuentas')}>Ver movimientos →</button></div>{balances.length ? balances.map(account=><div className="focus-row" key={account.id}><div className="avatar-soft">{account.account_type==='cash'?'$':'▤'}</div><div><b>{account.name}</b><small>{account.account_type==='cash'?'Efectivo':'Cuenta bancaria'}</small></div><strong>{money(account.balance)}</strong></div>) : <p className="empty-inline">No hay cuentas activas configuradas.</p>}</div>}
    </section>}
    <section className="dashboard-grid"><div className="surface-card"><div className="section-title"><div><span className="eyebrow">ACTIVIDAD RECIENTE</span><h2>Últimas cotizaciones</h2></div><button className="text-button" onClick={() => onView('cotizaciones')}>Ver todas →</button></div>{recent.length ? <div className="recent-list">{recent.map(item => <article className="recent-row" key={item.id}><span className="avatar-soft">{initials(item.customer?.name || 'AE')}</span><div className="recent-person"><b>{item.customer?.name || 'Cliente'}</b><small>{item.folio} · {item.panel_count} paneles</small></div><span className={`status-chip status-${item.status}`}>{!item.pricing_approved ? 'Precio pendiente' : labelStatus(item.status)}</span><b className="recent-amount">{money(item.total)}</b></article>)}</div> : <EmptyState title="Todavía no hay cotizaciones" body="Crea una propuesta para verla aquí." action="Crear cotización" onClick={() => onView('cotizaciones')}/>}</div>
      <div className="surface-card focus-card"><div className="section-title"><div><span className="eyebrow">SIGUIENTE ACCIÓN</span><h2>Seguimientos</h2></div><button className="text-button" onClick={() => onView('seguimientos')}>Ver todos →</button></div>{followups.slice(0, 4).map(item => <div className="focus-row" key={item.id}><div className="date-tile"><b>{new Date(`${item.due_date}T12:00:00`).getDate()}</b><small>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { month: 'short' }).toUpperCase()}</small></div><div><b>{item.customer?.name || 'Cliente'}</b><small>{item.note || 'Seguimiento'}</small></div><button className="check-button" title="Completar seguimiento" onClick={() => onComplete(item)}>✓</button><button className="focus-person" title="Abrir cliente" onClick={() => item.customer && onCustomer(item.customer)}>↗</button></div>)}{!followups.length && <EmptyState title="Sin seguimientos pendientes" body="Programa el próximo contacto desde la ficha del cliente."/>}</div></section>
  </>;
}

function CustomersView({ customers, search, onSearch, canCreate, onCreate, onSelect }: { customers: Customer[]; search: string; onSearch: (s: string) => void; canCreate: boolean; onCreate: () => void; onSelect: (c: Customer) => void }) {
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">CARTERA COMERCIAL</span><h2>{customers.length} contactos</h2></div><div className="toolbar-actions"><input className="search-input" value={search} onChange={event => onSearch(event.target.value)} placeholder="Buscar por nombre, ciudad o contacto"/>{canCreate && <button className="button button-primary" onClick={onCreate}>＋ Agregar cliente</button>}</div></div>{customers.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>CLIENTE</th><th>UBICACIÓN</th><th>CONTACTO</th><th>ESTADO</th><th>ORIGEN</th><th/></tr></thead><tbody>{customers.map(item => <tr key={item.id} onClick={() => onSelect(item)}><td><span className="table-person"><i>{initials(item.name)}</i><b>{item.name}<small>{item.email || 'Sin correo registrado'}</small></b></span></td><td>{item.city || '—'}<small className="sub-cell">{item.address || 'Domicilio pendiente'}</small></td><td>{item.phone || '—'}</td><td><span className="status-chip status-draft">{labelCustomerStatus(item.status)}</span></td><td>{item.source === 'public_web' ? 'Web pública' : 'Equipo'}</td><td><button className="icon-button" aria-label={`Ver ${item.name}`}>→</button></td></tr>)}</tbody></table></div> : <EmptyState title="No encontramos contactos" body="Cambia la búsqueda o agrega un nuevo prospecto." action={canCreate ? 'Agregar cliente' : undefined} onClick={onCreate}/>}</section>;
}

function QuotesView({ quotes, onCreate, onDownload, onShare, onMarkSent, onAccept, canWrite }: { quotes: Quote[]; onCreate: () => void; onDownload: (q: Quote) => void; onShare: (q: Quote) => void; onMarkSent: (q: Quote) => void; onAccept: (q: Quote) => void; canWrite: boolean }) {
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">PROPUESTAS SOLARES</span><h2>{quotes.length} cotizaciones</h2></div>{canWrite && <button className="button button-primary" onClick={onCreate}>＋ Nueva cotización</button>}</div>{quotes.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>FOLIO / CLIENTE</th><th>SISTEMA</th><th>INSTALACIÓN</th><th>INVERSIÓN</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{quotes.map(item => <tr key={item.id}><td><b>{item.folio}</b><small className="sub-cell">{item.customer?.name || 'Cliente'}</small></td><td>{item.panel_count} paneles · {((item.panel_count * item.panel_watts) / 1000).toFixed(1)} kWp<small className="sub-cell">{item.inverter}</small></td><td>{item.installation_city || item.customer?.city || '—'}<small className="sub-cell">{item.installation_address || item.customer?.address || 'Domicilio pendiente'}</small></td><td><b>{money(item.total)}</b>{!item.pricing_approved && <small className="price-review-note">Paquete pendiente de aprobación</small>}</td><td><span className={`status-chip status-${item.status}`}>{labelStatus(item.status)}</span></td><td><div className="row-actions"><button title="Descargar PDF" onClick={() => onDownload(item)}>PDF</button><button title="Abrir WhatsApp" onClick={() => onShare(item)}>WhatsApp</button>{item.status === 'draft' && canWrite && <button title="Marcar como enviada" onClick={() => onMarkSent(item)}>Marcar enviada</button>}{item.status === 'sent' && canWrite && <button title="Registrar que el cliente aceptó" onClick={() => onAccept(item)}>Registrar aceptación</button>}</div></td></tr>)}</tbody></table></div> : <EmptyState title="Crea tu primera cotización" body="Elige un cliente y un paquete de paneles para generar el PDF foliado." action={canWrite ? 'Nueva cotización' : undefined} onClick={onCreate}/>}</section>;
}

function FollowupsView({ items, onComplete, onCustomer }: { items: FollowUp[]; onComplete: (f: FollowUp) => void; onCustomer: (c: Customer) => void }) {
  const today = new Date().toISOString().slice(0, 10);
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">BITÁCORA COMERCIAL</span><h2>{items.length} próximos contactos</h2></div></div>{items.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>CLIENTE</th><th>NOTA DE SEGUIMIENTO</th><th>RESPONSABLE</th><th>ESTADO</th><th/></tr></thead><tbody>{items.map(item => <tr key={item.id}><td>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</td><td><button className="link-button" onClick={() => item.customer && onCustomer(item.customer)}>{item.customer?.name || 'Cliente'}</button><small className="sub-cell">{item.customer?.city}</small></td><td>{item.note || 'Retomar conversación'}</td><td>{item.assigned_to || 'Responsable pendiente'}</td><td><span className={`status-chip ${item.due_date <= today ? 'status-overdue' : 'status-sent'}`}>{item.due_date < today ? 'Vencido' : item.due_date === today ? 'Hoy' : 'Programado'}</span></td><td><button className="button button-small button-outline" onClick={() => onComplete(item)}>Completar</button></td></tr>)}</tbody></table></div> : <EmptyState title="No tienes seguimientos pendientes" body="Desde una ficha de cliente puedes programar una fecha y agregar una nota de bitácora."/>}</section>;
}

const expenseCategories = ['Nómina', 'Combustible', 'Impuestos', 'Intereses', 'Préstamos', 'Mantenimiento', 'Servicios', 'Viáticos', 'Materiales', 'Otro'];
function ExpensesView({ items, installations, accounts, canWrite, onSubmit }: { items: ProjectExpense[]; installations: Installation[]; accounts: FinancialAccount[]; canWrite: boolean; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  const today = new Date().toISOString().slice(0, 10);
  const month = today.slice(0, 7);
  const monthTotal = items.filter(item => item.occurred_on.startsWith(month)).reduce((sum, item) => sum + Number(item.amount), 0);
  return <div className="dashboard-grid"><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">CONTROL DE GASTOS</span><h2>Gastos del mes</h2></div><strong>{money(monthTotal)}</strong></div>{canWrite&&<><p className="muted-copy">Registra gastos operativos, enlazando la salida con la cuenta de caja o banco que realizó el pago.</p><form className="team-form" onSubmit={onSubmit}><h3>Nuevo gasto</h3><Field label="Fecha" name="occurred_on" type="date" defaultValue={today} required/><label className="field"><span>Categoría</span><select name="category" defaultValue="Otro" required>{expenseCategories.map(category=><option key={category}>{category}</option>)}</select></label><Field className="span-two" label="Descripción" name="description" required placeholder="Concepto y detalle del gasto"/><Field label="Importe (MXN)" name="amount" type="number" min="0.01" step="0.01" required/><label className="field"><span>Proyecto / instalación (opcional)</span><select name="installation_id" defaultValue=""><option value="">Gasto operativo general</option>{installations.map(item=><option key={item.id} value={item.id}>{item.customer?.name || 'Proyecto'} · {item.customer?.city || item.status}</option>)}</select></label><label className="field"><span>Cuenta que pagó</span><select name="account_id" required defaultValue=""><option value="">Selecciona caja o banco</option>{accounts.map(account=><option key={account.id} value={account.id}>{account.name} · {money(Number(account.current_balance))}</option>)}</select>{!accounts.length&&<small className="muted-copy">Registra primero una cuenta de caja o banco.</small>}</label><Field className="span-two" label="Enlace a comprobante (opcional)" name="receipt_url" type="url" placeholder="https://…"/><button className="button button-primary" disabled={!accounts.length}>Registrar gasto</button></form></>}</section><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">BITÁCORA FINANCIERA</span><h2>{items.length} movimientos</h2></div></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>CATEGORÍA / DESCRIPCIÓN</th><th>PROYECTO</th><th>RESPONSABLE</th><th>CUENTA / ESTADO</th><th>IMPORTE</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{new Date(`${item.occurred_on}T12:00:00`).toLocaleDateString('es-MX')}</td><td><b>{item.category}</b><small className="sub-cell">{item.description}{item.receipt_url&&<> · <a href={item.receipt_url} target="_blank" rel="noreferrer">Comprobante ↗</a></>}</small></td><td>{item.project_customer}<small className="sub-cell">{item.project_city || 'Operación general'}</small></td><td>{item.created_by}</td><td>{item.account_name || 'Sin salida de caja registrada'}</td><td>{money(Number(item.amount))}</td></tr>)}</tbody></table>{!items.length&&<EmptyState title="Sin gastos registrados" body="Agrega gastos operativos y costos directos para llevar su historial por fecha y proyecto."/>}</div></section></div>;
}

function AccountsView({ accounts, selectedId, onSelect, movements, canManage, canWrite, onCreateAccount, onCreateMovement, onReverse }: { accounts: FinancialAccount[]; selectedId: string; onSelect: (id: string) => void; movements: CashMovement[]; canManage: boolean; canWrite: boolean; onCreateAccount: (event: FormEvent<HTMLFormElement>) => void; onCreateMovement: (event: FormEvent<HTMLFormElement>) => void; onReverse: (movement: CashMovement) => void }) {
  const selected = accounts.find(account => account.id === selectedId);
  const today = new Date().toISOString().slice(0, 10);
  return <div className="dashboard-grid"><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">EFECTIVO DISPONIBLE</span><h2>{accounts.length} cuentas activas</h2></div></div>{accounts.length ? <div className="dashboard-grid">{accounts.map(account=><button key={account.id} className={`metric-card ${selectedId===account.id?'selected':''}`} onClick={()=>onSelect(account.id)}><small>{account.account_type==='cash'?'CAJA':'CUENTA DE DÉBITO'}</small><b>{account.name}</b><strong>{money(Number(account.current_balance))}</strong><span>Saldo inicial {money(Number(account.opening_balance))}</span></button>)}</div> : <EmptyState title="Aún no hay cuentas registradas" body="Agrega las cajas y cuentas bancarias reales para comenzar su control."/>}{canManage&&<form className="team-form" onSubmit={onCreateAccount}><h3>Registrar cuenta</h3><Field label="Nombre" name="name" required placeholder="Caja principal / Banco…"/><label className="field"><span>Tipo</span><select name="account_type"><option value="cash">Efectivo</option><option value="bank">Débito / Banco</option></select></label><Field label="Saldo inicial (MXN)" name="opening_balance" type="number" min="0" step="0.01" defaultValue={0} required/><Field label="Fecha del saldo inicial" name="opening_balance_date" type="date" defaultValue={today} required/><button className="button button-primary">Guardar cuenta</button></form>}</section><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">MOVIMIENTOS DE CUENTA</span><h2>{selected?.name || 'Selecciona una cuenta'}</h2></div>{selected&&<strong>{money(Number(selected.current_balance))}</strong>}</div>{selected&&canWrite&&<form className="team-form" onSubmit={onCreateMovement}><h3>Registrar entrada o salida</h3><label className="field"><span>Movimiento</span><select name="direction"><option value="in">Entrada de dinero</option><option value="out">Salida de dinero</option></select></label><Field label="Fecha" name="occurred_on" type="date" defaultValue={today} required/><Field label="Importe (MXN)" name="amount" type="number" min="0.01" step="0.01" required/><Field label="Categoría" name="category" required placeholder="Cobranza, gasto, ajuste…"/><Field className="span-two" label="Detalle" name="description" required placeholder="Motivo y referencia del movimiento"/><button className="button button-primary">Registrar movimiento</button></form>}{selected&&<div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>MOVIMIENTO</th><th>DETALLE</th><th>RESPONSABLE</th><th>IMPORTE</th><th/></tr></thead><tbody>{movements.map(item=>{const reversed=movements.some(row=>row.reversal_of_id===item.id);return <tr key={item.id}><td>{new Date(`${item.occurred_on}T12:00:00`).toLocaleDateString('es-MX')}</td><td><span className={`status-chip ${item.direction==='in'?'status-approved':'status-overdue'}`}>{item.direction==='in'?'Entrada':'Salida'}</span></td><td><b>{item.category}</b><small className="sub-cell">{item.description}{item.reversal_of_id&&' · Reversa'}</small></td><td>{item.created_by}</td><td>{item.direction==='in'?'+':'−'}{money(Number(item.amount))}</td><td>{canWrite&&!reversed&&item.source_type!=='reversal'&&<button className="button button-small button-outline" onClick={()=>onReverse(item)}>Corregir</button>}</td></tr>;})}</tbody></table>{!movements.length&&<EmptyState title="Sin movimientos de cuenta" body="El saldo inicial y cada entrada o salida se conservan para consulta."/>}</div>}</section></div>;
}

function SuppliersView({ items, canWrite, onSubmit }: { items: Supplier[]; canWrite: boolean; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <div className="dashboard-grid"><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">CATÁLOGO DE COMPRAS</span><h2>{items.length} proveedores</h2></div></div>{canWrite&&<form className="team-form" onSubmit={onSubmit}><h3>Nuevo proveedor</h3><Field className="span-two" label="Razón social / nombre" name="name" required/><Field label="RFC" name="rfc"/><Field label="Teléfono" name="phone" type="tel"/><Field label="Correo" name="email" type="email"/><label className="field"><span>Condiciones habituales</span><select name="payment_terms"><option value="cash">Contado</option><option value="credit">Crédito</option></select></label><Field label="Días de crédito" name="credit_days" type="number" min="0" max="365" defaultValue={0}/><button className="button button-primary">Guardar proveedor</button></form>}</section><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">PROVEEDORES</span><h2>Condiciones comerciales</h2></div></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROVEEDOR</th><th>RFC / CONTACTO</th><th>CONDICIÓN</th><th>SALDO POR PAGAR</th><th>ESTADO</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td><b>{item.name}</b><small className="sub-cell">{item.email}</small></td><td>{item.rfc||'RFC pendiente'}<small className="sub-cell">{item.phone}</small></td><td>{item.payment_terms==='credit'?`Crédito · ${item.credit_days} días`:'Contado'}</td><td><b>{money(Number(item.current_balance))}</b></td><td><span className={`status-chip ${item.active?'status-approved':'status-overdue'}`}>{item.active?'Activo':'Inactivo'}</span></td></tr>)}</tbody></table>{!items.length&&<EmptyState title="Sin proveedores registrados" body="Agrega los proveedores y sus condiciones para usarlos en compras."/>}</div><p className="muted-copy">El saldo por pagar se calcula con las compras y los pagos vinculados.</p></section></div>;
}

function PurchasesView({ items, suppliers, inventory, accounts, canWrite, token, onItems, onSuppliers, onAccounts, onInventory, announce }: { items: Purchase[]; suppliers: Supplier[]; inventory: InventoryItem[]; accounts: FinancialAccount[]; canWrite: boolean; token: string; onItems: (rows: Purchase[]) => void; onSuppliers: (rows: Supplier[]) => void; onAccounts: (rows: FinancialAccount[]) => void; onInventory: (rows: InventoryItem[]) => void; announce: (message: string, type?: Notice['type']) => void }) {
  const today = new Date().toISOString().slice(0, 10);
  const [lines, setLines] = useState([{ item_id: '', quantity: '1', unit_cost: '' }]);
  const [paymentPurchase, setPaymentPurchase] = useState<Purchase | null>(null);
  const [correctionPayment, setCorrectionPayment] = useState<{ purchase: Purchase; payment: NonNullable<Purchase['payments']>[number] } | null>(null);
  const [terms, setTerms] = useState<'cash' | 'credit'>('cash');
  const [supplierId, setSupplierId] = useState('');
  const [initialPayment, setInitialPayment] = useState('0');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [purchaseDate, setPurchaseDate] = useState(today);
  const [cfdiProposal, setCfdiProposal] = useState<CfdiProposal|null>(null);
  const [cfdiBusy, setCfdiBusy] = useState(false);
  const [cfdiError, setCfdiError] = useState('');
  const supplier = suppliers.find(item => item.id === supplierId);
  const total = lines.reduce((sum, line) => sum + Number(line.quantity || 0) * Number(line.unit_cost || 0), 0);
  const materialSummary = lines.filter(line => line.item_id).map(line => {
    const item = inventory.find(row => row.id === line.item_id);
    return `${item?.name || 'Artículo'} +${line.quantity} ${item?.unit || ''}`.trim();
  }).join(' · ');
  const normalizedCode = (value:string) => value.trim().toLocaleUpperCase();
  const cfdiSupplierMatches = !cfdiProposal || normalizedCode(supplier?.rfc||'') === normalizedCode(cfdiProposal.supplier_rfc);
  const cfdiLinesMapped = !cfdiProposal || lines.every(line => Boolean(line.item_id));
  const cfdiTotalMatches = !cfdiProposal || Math.abs(Math.round(total*100)-Math.round(Number(cfdiProposal.declared_total)*100)) <= 1;
  const canSubmitPurchase = !cfdiProposal || (cfdiSupplierMatches && cfdiLinesMapped && cfdiTotalMatches);

  async function reload() {
    const [purchaseRows, supplierRows, accountRows, inventoryRows] = await Promise.all([
      request<Purchase[]>('/purchases', token), request<Supplier[]>('/suppliers', token),
      request<FinancialAccount[]>('/accounts', token), request<InventoryItem[]>('/inventory', token),
    ]);
    onItems(purchaseRows); onSuppliers(supplierRows); onAccounts(accountRows); onInventory(inventoryRows);
  }

  async function submitPurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    try {
      const purchase = await request<Purchase>('/purchases', token, { method: 'POST', body: JSON.stringify({
        supplier_id: supplierId, invoice_number: String(data.get('invoice_number') || '').trim(), payment_terms: terms,
        purchase_date: String(data.get('purchase_date')), due_date: String(data.get('due_date') || '') || null,
        lines: lines.map(line => ({ item_id: line.item_id, quantity: Number(line.quantity), unit_cost: Number(line.unit_cost) })),
        initial_payment: Number(data.get('initial_payment') || 0), payment_account_id: String(data.get('payment_account_id') || '') || null,
        payment_reference: String(data.get('payment_reference') || '').trim(),
      }) });
      onItems([purchase, ...items]); form.reset(); setLines([{ item_id: '', quantity: '1', unit_cost: '' }]);
      setSupplierId(''); setTerms('cash'); setInitialPayment('0'); setInvoiceNumber(''); setPurchaseDate(today); setCfdiProposal(null); setCfdiError('');
      const [, supplierRows, accountRows, inventoryRows] = await Promise.all([
        request<Purchase[]>('/purchases', token).then(onItems), request<Supplier[]>('/suppliers', token),
        request<FinancialAccount[]>('/accounts', token), request<InventoryItem[]>('/inventory', token),
      ]);
      onSuppliers(supplierRows); onAccounts(accountRows); onInventory(inventoryRows);
      announce(`Compra ${purchase.folio} registrada; el almacén y el saldo del proveedor se actualizaron.`);
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo registrar la compra.', 'error'); }
  }

  async function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!paymentPurchase) return;
    const form = event.currentTarget; const data = new FormData(form);
    try {
      const updated = await request<Purchase>(`/purchases/${paymentPurchase.id}/payments`, token, { method: 'POST', body: JSON.stringify({ amount: Number(data.get('amount')), account_id: String(data.get('account_id')), paid_on: String(data.get('paid_on')), reference: String(data.get('reference') || '') }) });
      onItems(items.map(item => item.id === updated.id ? updated : item)); setPaymentPurchase(null); await reload(); announce(`Pago aplicado a ${updated.folio}; caja y saldo de proveedor actualizados.`);
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo registrar el pago.', 'error'); }
  }

  async function submitPaymentCorrection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!correctionPayment) return;
    const form = event.currentTarget; const reason = String(new FormData(form).get('reason') || '').trim();
    try {
      await request<Purchase>(`/purchases/${correctionPayment.purchase.id}/payments/${correctionPayment.payment.id}/reverse`, token, { method: 'POST', body: JSON.stringify({ reason }) });
      setCorrectionPayment(null); await reload(); announce('Corrección registrada; el pago original se conserva en el historial y caja/proveedor se actualizaron.');
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo corregir el pago.', 'error'); }
  }

  async function importCfdi(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setCfdiError(''); setCfdiBusy(true);
    try {
      if (!file.name.toLowerCase().endsWith('.xml')) throw new Error('Selecciona el XML CFDI de la factura.');
      if (file.size > 2 * 1024 * 1024) throw new Error('El archivo XML debe ser menor a 2 MiB.');
      const xml = await file.text();
      const proposal = await request<CfdiProposal>('/purchases/parse-cfdi', token, { method:'POST', body:JSON.stringify({xml}) });
      const importedLines = proposal.concepts.map(concept => {
        const identifier = normalizedCode(concept.identifier);
        const exactMatches = inventory.filter(item => identifier && [item.barcode, item.model].some(code => normalizedCode(code||'') === identifier));
        const match = exactMatches.length === 1 ? exactMatches[0] : undefined;
        return { item_id:match?.id||'', quantity:String(concept.quantity), unit_cost:String(concept.unit_cost_before_global_adjustments) };
      });
      const supplierMatches = suppliers.filter(item => item.active && normalizedCode(item.rfc) === normalizedCode(proposal.supplier_rfc));
      const matchedSupplier = supplierMatches.length === 1 ? supplierMatches[0] : undefined;
      setCfdiProposal(proposal); setLines(importedLines); setInvoiceNumber(proposal.invoice_reference); setPurchaseDate(proposal.purchase_date);
      if (matchedSupplier) { setSupplierId(matchedSupplier.id); setTerms(matchedSupplier.payment_terms); setInitialPayment(matchedSupplier.payment_terms === 'cash' ? String(importedLines.reduce((sum,line)=>sum+Number(line.quantity)*Number(line.unit_cost),0)) : '0'); }
      else if (supplierMatches.length > 1) setCfdiError('Hay varios proveedores activos con ese RFC; selecciona el proveedor correcto y valida el registro duplicado.');
      announce(`CFDI leído. Revisa proveedor, artículos, importes y cuenta antes de registrar la compra. ${importedLines.filter(line=>line.item_id).length} de ${importedLines.length} artículos identificados.`);
    } catch(error) { setCfdiProposal(null); setCfdiError(error instanceof Error?error.message:'No se pudo leer el XML CFDI.'); }
    finally { setCfdiBusy(false); }
  }

  return <>
    {canWrite && <section className="surface-card table-surface purchase-entry"><div className="section-title"><div><span className="eyebrow">ENTRADA DE ALMACÉN + CUENTAS POR PAGAR</span><h2>Registrar compra de materiales</h2></div></div>
      <form className="form-grid" onSubmit={submitPurchase}>
        <div className="cfdi-import span-two"><label className="field"><span>Precargar desde XML CFDI (opcional)</span><input type="file" accept=".xml,application/xml,text/xml" onChange={event=>void importCfdi(event)} disabled={cfdiBusy}/></label><small>El archivo se procesa para proponer datos; no se guarda. Confirma proveedor, artículos, cantidades e importes antes de registrar.</small>{cfdiBusy&&<p role="status">Leyendo factura…</p>}{cfdiError&&<p className="error-message" role="alert">{cfdiError}</p>}{cfdiProposal&&<div className="cfdi-review"><div><b>CFDI leído · revisión requerida</b><button type="button" className="text-button" onClick={()=>{setCfdiProposal(null);setCfdiError('');}}>Quitar precarga</button></div><p>{cfdiProposal.supplier_name||'Proveedor sin nombre'} · RFC {cfdiProposal.supplier_rfc} · {cfdiProposal.invoice_reference} · {cfdiProposal.purchase_date}</p><p>Subtotal declarado {money(Number(cfdiProposal.declared_subtotal))} · Descuento global {money(Number(cfdiProposal.global_discount))} · Total factura {money(Number(cfdiProposal.declared_total))}</p><p>{lines.filter(line=>line.item_id).length}/{lines.length} conceptos relacionados a artículos. Importe de compra revisado: {money(total)}.</p>{(!cfdiSupplierMatches||!cfdiLinesMapped||!cfdiTotalMatches)&&<p className="cfdi-warning">No se puede registrar esta precarga hasta relacionar cada artículo, seleccionar el proveedor con RFC coincidente y hacer coincidir el total. Impuestos, descuentos globales y fletes no se distribuyen automáticamente; ajusta los costos con la regla del contador o quita la precarga para capturarla manualmente.</p>}{cfdiProposal.requires_accounting_review&&<p className="cfdi-warning">El total incluye diferencia contra el subtotal neto de conceptos. Revisa tratamiento de impuestos/ajustes antes de confirmar.</p>}</div>}</div>
        <label className="field span-two"><span>Proveedor</span><select value={supplierId} onChange={event => { const value = event.target.value; setSupplierId(value); const selected = suppliers.find(row => row.id === value); setTerms(selected?.payment_terms || 'cash'); setInitialPayment(selected?.payment_terms === 'cash' ? String(total) : '0'); }} required><option value="">Selecciona proveedor</option>{suppliers.filter(item => item.active).map(item => <option key={item.id} value={item.id}>{item.name} · {item.payment_terms === 'credit' ? `Crédito ${item.credit_days} días` : 'Contado'}</option>)}</select>{!suppliers.length && <small className="muted-copy">Registra primero un proveedor en el apartado Proveedores.</small>}</label>
        <Field label="Factura / referencia" name="invoice_number" value={invoiceNumber} onChange={setInvoiceNumber} placeholder="Folio de factura"/><Field label="Fecha de compra" name="purchase_date" type="date" value={purchaseDate} onChange={setPurchaseDate} required/>
        <label className="field"><span>Forma acordada</span><select value={terms} onChange={event => { const value = event.target.value as 'cash' | 'credit'; setTerms(value); setInitialPayment(value === 'cash' ? String(total) : '0'); }}><option value="cash">Contado</option><option value="credit" disabled={!supplier?.credit_days}>Crédito</option></select></label>
        {terms === 'credit' && <Field label="Fecha límite de pago" name="due_date" type="date" defaultValue={supplier?.credit_days ? new Date(Date.now() + supplier.credit_days * 86400000).toISOString().slice(0, 10) : ''} min={today}/>}
        <div className="span-two purchase-lines"><div className="panel-head"><div><h3>Material recibido</h3><p>Los precios quedan guardados en cada movimiento del kardex.</p></div><button type="button" className="button button-outline" onClick={() => setLines(rows => [...rows, { item_id: '', quantity: '1', unit_cost: '' }])}>＋ Agregar artículo</button></div>
          {lines.map((line, index) => <div className="purchase-line" key={index}><label className="field"><span>Artículo</span><select value={line.item_id} onChange={event => { const selectedItem = inventory.find(row => row.id === event.target.value); setLines(rows => rows.map((row, i) => i === index ? { ...row, item_id: event.target.value, unit_cost: row.unit_cost || String(selectedItem?.unit_cost || '') } : row)); }} required><option value="">Selecciona material</option>{inventory.map(item => <option key={item.id} value={item.id}>{item.name} · stock {item.quantity} {item.unit}</option>)}</select></label><Field label="Cantidad" type="number" min="0.01" step="0.01" value={line.quantity} onChange={value => setLines(rows => rows.map((row, i) => i === index ? { ...row, quantity: value } : row))} required/><Field label="Costo unitario MXN" type="number" min="0.01" step="0.01" value={line.unit_cost} onChange={value => setLines(rows => rows.map((row, i) => i === index ? { ...row, unit_cost: value } : row))} required/>{lines.length > 1 && <button type="button" className="icon-button" aria-label="Quitar artículo" onClick={() => setLines(rows => rows.filter((_, i) => i !== index))}>×</button>}</div>)}
        </div>
        <div className="quote-total span-two"><div><small>TOTAL DE COMPRA</small><strong>{money(total)}</strong><span>{lines.length} renglones de material</span></div></div>
        <Field label={terms === 'cash' ? 'Importe pagado' : 'Anticipo (opcional)'} name="initial_payment" type="number" min="0" step="0.01" value={terms === 'cash' ? String(total) : initialPayment} onChange={setInitialPayment} required/>
        <label className="field"><span>Cuenta de pago</span><select name="payment_account_id" required={terms === 'cash' || Number(initialPayment) > 0}><option value="">Selecciona una cuenta</option>{accounts.map(account => <option key={account.id} value={account.id}>{account.name} · {money(Number(account.current_balance))}</option>)}</select></label>
        <Field label="Referencia del pago" name="payment_reference" placeholder="Transferencia, recibo…"/>
        <div className="impact-note span-two" role="note"><b>Impacto al confirmar esta compra</b><span>Almacén: {materialSummary || 'los artículos y cantidades seleccionados aumentarán las existencias'}.</span><span>Proveedor: la cuenta por pagar recibe el saldo de {money(Math.max(0, total - (terms === 'cash' ? total : Number(initialPayment || 0))))}.</span><span>Caja/banco: disminuye {money(terms === 'cash' ? total : Number(initialPayment || 0))} por el pago inicial registrado.</span><small>El saldo mostrado refleja total y anticipo capturados; impuestos, descuentos globales y fletes no se distribuyen automáticamente.</small></div>
        <div className="modal-actions span-two"><button className="button button-primary" disabled={!supplier || !inventory.length || !accounts.length || !canSubmitPurchase}>Registrar compra</button></div>
      </form>
    </section>}
    <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">COMPRAS REGISTRADAS</span><h2>{items.length} compras · {money(items.reduce((sum, item) => sum + Number(item.balance), 0))} por pagar</h2></div></div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>FOLIO / PROVEEDOR</th><th>FACTURA / MATERIALES</th><th>FECHAS</th><th>TOTAL</th><th>PAGADO / HISTORIAL</th><th>SALDO</th><th>ESTADO</th><th/></tr></thead><tbody>{items.map(item => <tr key={item.id}><td><b>{item.folio}</b><small className="sub-cell">{item.supplier?.name || 'Proveedor'}</small></td><td>{item.invoice_number || 'Sin factura'}<small className="sub-cell">{item.lines.map(line => `${line.item_name} × ${line.quantity}`).join(' · ')}</small></td><td>{new Date(`${item.purchase_date}T12:00:00`).toLocaleDateString('es-MX')}<small className="sub-cell">{item.due_date ? `Vence ${new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX')}` : 'Contado'}</small></td><td><b>{money(Number(item.total))}</b></td><td>{money(Number(item.paid_amount))}<div className="payment-history">{(item.payments||[]).map(payment=><div key={payment.id}><span>{new Date(`${payment.paid_on}T12:00:00`).toLocaleDateString('es-MX')} · {money(Number(payment.amount))}{payment.is_reversal?' · Corrección':''}{payment.reference?` · ${payment.reference}`:''}</span>{canWrite&&payment.can_reverse&&<button type="button" className="text-button" onClick={()=>setCorrectionPayment({purchase:item,payment})}>Corregir</button>}</div>)}</div></td><td><b>{money(Number(item.balance))}</b></td><td><span className={`status-chip ${item.status === 'paid' ? 'status-approved' : 'status-overdue'}`}>{item.status === 'paid' ? 'Pagada' : item.status === 'partially_paid' ? 'Pago parcial' : 'Pendiente'}</span></td><td>{canWrite && Number(item.balance) > 0 && <button className="button button-small button-outline" onClick={() => setPaymentPurchase(item)}>Registrar pago</button>}</td></tr>)}</tbody></table>{!items.length && <EmptyState title="Sin compras registradas" body="Al registrar una compra, sus renglones aumentan existencias y el saldo se vincula al proveedor."/>}</div>
    </section>
    {paymentPurchase && <Modal title={`Pago a ${paymentPurchase.supplier?.name || 'proveedor'}`} subtitle={`Saldo pendiente: ${money(Number(paymentPurchase.balance))}`} onClose={() => setPaymentPurchase(null)}><form className="form-grid" onSubmit={submitPayment}><Field label="Importe" name="amount" type="number" min="0.01" max={Number(paymentPurchase.balance)} step="0.01" required/><Field label="Fecha de pago" name="paid_on" type="date" defaultValue={today} required/><label className="field span-two"><span>Cuenta de salida</span><select name="account_id" required><option value="">Selecciona caja o banco</option>{accounts.map(account => <option key={account.id} value={account.id}>{account.name} · {money(Number(account.current_balance))}</option>)}</select></label><div className="impact-note span-two" role="note"><b>Impacto al aplicar el pago</b><span>Caja/banco: disminuye el importe registrado en la cuenta seleccionada.</span><span>Proveedor: el saldo pendiente de {money(Number(paymentPurchase.balance))} baja por el mismo importe.</span><small>El pago queda ligado a la compra y al movimiento de caja para conservar su historial.</small></div><Field className="span-two" label="Referencia" name="reference" placeholder="Transferencia, recibo…"/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setPaymentPurchase(null)}>Cancelar</button><button className="button button-primary">Guardar pago</button></div></form></Modal>}
    {correctionPayment && <Modal title="Corregir pago a proveedor" subtitle={`${correctionPayment.purchase.folio} · ${money(Number(correctionPayment.payment.amount))}`} onClose={() => setCorrectionPayment(null)}><form className="form-grid" onSubmit={submitPaymentCorrection}><p className="muted-copy span-two">Se agregará una reversa enlazada al movimiento de caja y al pago original. El registro original no se borra.</p><label className="field span-two"><span>Motivo de la corrección</span><textarea name="reason" minLength={5} maxLength={120} required placeholder="Explica qué dato o movimiento se corrige…"/></label><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setCorrectionPayment(null)}>Cancelar</button><button className="button button-primary">Registrar corrección</button></div></form></Modal>}
  </>;
}

function SalesView({ items, quotes, inventory, installers, accounts, canWrite, token, onItems, onAccounts, onInventory, onRefresh, announce }: { items: Sale[]; quotes: Quote[]; inventory: InventoryItem[]; installers: Installer[]; accounts: FinancialAccount[]; canWrite: boolean; token: string; onItems: (rows: Sale[]) => void; onAccounts: (rows: FinancialAccount[]) => void; onInventory: (rows: InventoryItem[]) => void; onRefresh: () => Promise<void>; announce: (message: string, type?: Notice['type']) => void }) {
  const acceptedQuotes = quotes.filter(quote => quote.status === 'accepted' && quote.pricing_approved && !items.some(sale => sale.quote_id === quote.id));
  const [quoteId, setQuoteId] = useState('');
  const [saleType, setSaleType] = useState<'cash' | 'credit'>('cash');
  const [materials, setMaterials] = useState([{ item_id: '', quantity: '1' }]);
  const selectedQuote = acceptedQuotes.find(quote => quote.id === quoteId) || acceptedQuotes[0];

  async function submitSale(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    if (!selectedQuote) return;
    try {
      const assignedInstallers = data.getAll('assigned_installers').map(String);
      const created = await request<Sale>('/sales', token, { method: 'POST', body: JSON.stringify({
        quote_id: selectedQuote.id,
        sale_type: saleType,
        account_id: saleType === 'cash' ? String(data.get('account_id') || '') || null : null,
        due_date: saleType === 'credit' ? String(data.get('due_date') || '') || null : null,
        scheduled_at: String(data.get('scheduled_at') || '') ? new Date(String(data.get('scheduled_at'))).toISOString() : null,
        lead_installer: assignedInstallers[0] || '',
        assigned_installers: assignedInstallers,
        notes: String(data.get('notes') || '').trim(),
        materials: materials.map(line => ({ item_id: line.item_id, quantity: Number(line.quantity) })),
      }) });
      onItems([created, ...items]);
      const [accountRows, inventoryRows, saleRows] = await Promise.all([
        request<FinancialAccount[]>('/accounts', token), request<InventoryItem[]>('/inventory', token), request<Sale[]>('/sales', token),
      ]);
      onAccounts(accountRows); onInventory(inventoryRows); onItems(saleRows); await onRefresh();
      setMaterials([{ item_id: '', quantity: '1' }]); setQuoteId('');
      announce(`Venta ${created.folio} y orden ${created.installation?.folio || ''} registradas; caja/cartera y existencias se actualizaron.`);
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo registrar la venta y orden.', 'error'); }
  }

  return <>
    {canWrite && <section className="surface-card table-surface purchase-entry"><div className="section-title"><div><span className="eyebrow">VENTA ACEPTADA + ORDEN DE TRABAJO</span><h2>Registrar venta y asignar instalación</h2></div></div><p className="muted-copy">Este movimiento requiere cotización aceptada, materiales disponibles y una cuenta instaladora activa. La salida a almacén se registra contra la orden; el tratamiento de impuestos y pagos mixtos aún requiere definición contable.</p>{acceptedQuotes.length ? <form className="form-grid" onSubmit={submitSale}>
      <label className="field span-two"><span>Cotización aceptada</span><select value={quoteId || selectedQuote?.id || ''} onChange={event => setQuoteId(event.target.value)} required>{acceptedQuotes.map(quote => <option key={quote.id} value={quote.id}>{quote.folio} · {quote.customer?.name || 'Cliente'} · {money(Number(quote.total))}</option>)}</select></label>
      {selectedQuote && <div className="quote-total span-two"><div><small>TOTAL DE PROPUESTA</small><strong>{money(Number(selectedQuote.total))}</strong><span>{selectedQuote.customer?.name} · {selectedQuote.panel_count} paneles · {selectedQuote.installation_city}</span></div><span>{selectedQuote.payment_method}</span></div>}
      <label className="field"><span>Tipo de venta</span><select value={saleType} onChange={event => setSaleType(event.target.value as 'cash' | 'credit')}><option value="cash">Contado · liquidado</option><option value="credit">Crédito · saldo total a una fecha</option></select></label>
      {saleType === 'cash' ? <label className="field"><span>Cuenta que recibió el total</span><select name="account_id" required defaultValue=""><option value="">Selecciona caja o banco</option>{accounts.map(account => <option key={account.id} value={account.id}>{account.name} · {money(Number(account.current_balance))}</option>)}</select></label> : <Field label="Vencimiento del saldo" name="due_date" type="date" defaultValue={new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10)} required/>}
      <label className="field"><span>Cuadrilla instaladora</span><select name="assigned_installers" multiple required size={Math.min(5, Math.max(2, installers.length))}>{installers.map(item => <option key={item.email} value={item.email}>{item.name || item.email} · {item.email}</option>)}</select><small>Selecciona una o más cuentas instaladoras activas; la primera será responsable.</small></label>
      <Field label="Fecha de instalación" name="scheduled_at" type="datetime-local"/>
      <div className="span-two purchase-lines"><div className="panel-head"><div><h3>Material solicitado en la orden</h3><p>Las cantidades se validan contra almacén y se descuentan al registrar la venta.</p></div><button type="button" className="button button-outline" onClick={() => setMaterials(rows => [...rows, { item_id: '', quantity: '1' }])}>＋ Agregar material</button></div>
        {materials.map((line, index) => <div className="purchase-line" key={index}><label className="field"><span>Artículo</span><select value={line.item_id} onChange={event => setMaterials(rows => rows.map((row, i) => i === index ? { ...row, item_id: event.target.value } : row))} required><option value="">Selecciona material</option>{inventory.map(item => <option key={item.id} value={item.id}>{item.name} · {item.available_quantity ?? item.quantity} {item.unit} disponibles</option>)}</select></label><Field label="Cantidad" type="number" min="0.01" step="0.01" value={line.quantity} onChange={value => setMaterials(rows => rows.map((row, i) => i === index ? { ...row, quantity: value } : row))} required/>{materials.length > 1 && <button type="button" className="icon-button" aria-label="Quitar material" onClick={() => setMaterials(rows => rows.filter((_, i) => i !== index))}>×</button>}</div>)}
      </div>
      <Field className="span-two" label="Instrucciones de instalación / observaciones" name="notes" placeholder="Notas técnicas o indicaciones para la cuadrilla"/>
      {selectedQuote && <div className="impact-note span-two" role="note"><b>Impacto al confirmar esta venta</b><span>{saleType === 'cash' ? `Caja/banco: aumenta ${money(Number(selectedQuote.total))} en la cuenta seleccionada.` : `Clientes por cobrar: se registra un saldo inicial de ${money(Number(selectedQuote.total))} con el vencimiento elegido.`}</span><span>Almacén: las cantidades indicadas quedan reservadas para la orden; la existencia física baja cuando se registra la salida de material. Cantidades por encima de lo disponible se rechazan.</span><span>Proyecto: se genera una orden con folio y se asigna la cuadrilla seleccionada.</span><small>El resumen no incluye impuestos, pagos mixtos ni reglas de Plan 24; siguen pendientes de validación contable.</small></div>}
      <div className="modal-actions span-two"><button className="button button-primary" disabled={!installers.length || !inventory.length || (saleType === 'cash' && !accounts.length)}>Registrar venta y emitir orden</button></div>
    </form> : <EmptyState title="No hay cotizaciones aprobadas por registrar" body="Marca como aceptada una propuesta enviada y confirma que sus precios estén aprobados para crear la venta y la orden."/>}</section>}
    <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">VENTAS REGISTRADAS</span><h2>{items.length} ventas</h2></div></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FOLIO DE VENTA / CLIENTE</th><th>ORDEN DE TRABAJO</th><th>COBRO</th><th>MATERIALES SOLICITADOS</th><th>TOTAL</th><th>FECHA</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td><b>{item.folio}</b><small className="sub-cell">{item.customer?.name || 'Cliente'} · {item.quote?.folio}</small></td><td><b>{item.installation?.folio || 'Orden pendiente'}</b><small className="sub-cell">{item.installation?.lead_installer || 'Sin instalador'}{item.installation?.scheduled_at ? ` · ${new Date(item.installation.scheduled_at).toLocaleString('es-MX')}` : ''}</small></td><td><span className={`status-chip ${item.sale_type === 'cash' ? 'status-approved' : 'status-overdue'}`}>{item.sale_type === 'cash' ? 'Contado' : `Crédito · vence ${item.receivable?.due_date ? new Date(`${item.receivable.due_date}T12:00:00`).toLocaleDateString('es-MX') : 'por definir'}`}</span></td><td>{item.materials.map(line => `${line.item_name} × ${line.quantity}`).join(' · ')}</td><td><b>{money(Number(item.total))}</b></td><td>{new Date(item.created_at).toLocaleDateString('es-MX')}</td></tr>)}</tbody></table>{!items.length && <EmptyState title="Sin ventas registradas" body="Las propuestas aceptadas aparecen aquí para confirmar la operación y generar su orden de trabajo."/>}</div></section>
  </>;
}

function ReceivablesView({ items, customers, quotes, accounts, canWrite, token, onCreate, onItems, onAccounts, announce }: { items: Receivable[]; customers: Customer[]; quotes: Quote[]; accounts: FinancialAccount[]; canWrite: boolean; token: string; onCreate: (event: FormEvent<HTMLFormElement>) => void; onItems: (rows: Receivable[]) => void; onAccounts: (rows: FinancialAccount[]) => void; announce: (message: string, type?: Notice['type']) => void }) {
  const today = new Date().toISOString().slice(0, 10);
  const nextWeek = new Date(`${today}T00:00:00Z`); nextWeek.setUTCDate(nextWeek.getUTCDate() + 7);
  const nextWeekDate = nextWeek.toISOString().slice(0, 10);
  const [scheduleFilter, setScheduleFilter] = useState<'all' | 'overdue' | 'today' | 'upcoming' | 'paid'>('all');
  const [paymentReceivable, setPaymentReceivable] = useState<Receivable | null>(null);
  const [correctionPayment, setCorrectionPayment] = useState<{ receivable: Receivable; payment: NonNullable<Receivable['payments']>[number] } | null>(null);
  const openBalance = items.reduce((sum, item) => sum + Number(item.balance), 0);
  const overdueBalance = items.filter(item => item.status === 'overdue').reduce((sum, item) => sum + Number(item.balance), 0);
  const filteredReceivables = items.filter(item => {
    if (scheduleFilter === 'overdue') return item.balance > 0 && item.due_date < today;
    if (scheduleFilter === 'today') return item.balance > 0 && item.due_date === today;
    if (scheduleFilter === 'upcoming') return item.balance > 0 && item.due_date > today && item.due_date <= nextWeekDate;
    if (scheduleFilter === 'paid') return item.balance <= 0;
    return true;
  });

  async function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!paymentReceivable) return;
    const form = event.currentTarget; const data = new FormData(form);
    try {
      await request<Receivable>(`/receivables/${paymentReceivable.id}/payments`, token, { method: 'POST', body: JSON.stringify({ amount: Number(data.get('amount')), account_id: String(data.get('account_id')), paid_on: String(data.get('paid_on')), reference: String(data.get('reference') || '') }) });
      const [rows, accountRows] = await Promise.all([request<Receivable[]>('/receivables', token), request<FinancialAccount[]>('/accounts', token)]);
      onItems(rows); onAccounts(accountRows); setPaymentReceivable(null); announce('Cobranza guardada y entrada aplicada a caja o banco.');
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo aplicar el pago.', 'error'); }
  }

  async function submitPaymentCorrection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!correctionPayment) return;
    const reason = String(new FormData(event.currentTarget).get('reason') || '').trim();
    try {
      await request<Receivable>(`/receivables/${correctionPayment.receivable.id}/payments/${correctionPayment.payment.id}/reverse`, token, { method: 'POST', body: JSON.stringify({ reason }) });
      const [rows, accountRows] = await Promise.all([request<Receivable[]>('/receivables', token), request<FinancialAccount[]>('/accounts', token)]);
      onItems(rows); onAccounts(accountRows); setCorrectionPayment(null);
      announce('Corrección registrada; el pago original se conserva en el historial y la cuenta por cobrar/caja se actualizaron.');
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo corregir el pago.', 'error'); }
  }

  function shareReminder(item: Receivable) {
    if (!item.customer?.phone) return;
    const digits = item.customer.phone.replace(/\D/g, '');
    const phone = digits.length === 10 ? `52${digits}` : digits;
    const dateLabel = new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'long' });
    const overdueDays = item.due_date < today ? Math.floor((Date.parse(`${today}T00:00:00Z`) - Date.parse(`${item.due_date}T00:00:00Z`)) / 86400000) : 0;
    const situation = item.due_date < today ? `está vencido desde el ${dateLabel} (${overdueDays} ${overdueDays === 1 ? 'día' : 'días'} de atraso)` : item.due_date === today ? 'vence el día de hoy' : item.due_date <= nextWeekDate ? `vence próximamente, el ${dateLabel}` : `tiene fecha de vencimiento el ${dateLabel}`;
    const method = item.payment_method ? ` Forma acordada: ${item.payment_method}.` : '';
    const message = `Hola ${item.customer.name}, te escribimos de Arco Energy para recordarte la cuota ${item.installment_number} por ${money(Number(item.balance))}, que ${situation}.${method} Si ya realizaste el pago, compártenos el comprobante. ¡Gracias!`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank', 'noopener,noreferrer');
  }

  return <>
    <div className="metric-grid"><Metric label="CARTERA ABIERTA" value={money(openBalance)} note={`${items.filter(item => item.balance > 0).length} saldos pendientes`} icon="$" tone="rose"/><Metric label="VENCIDO" value={money(overdueBalance)} note="Saldo con fecha vencida" icon="!" tone="amber"/><Metric label="CUENTAS REGISTRADAS" value={String(items.length)} note="Cuotas y saldos capturados" icon="↙" tone="blue"/></div>
    {canWrite && <section className="surface-card table-surface purchase-entry"><div className="section-title"><div><span className="eyebrow">CARTERA DE CLIENTES</span><h2>Registrar saldo por cobrar</h2></div></div><p className="muted-copy">Captura la cuota acordada con el cliente. La integración automática con ventas y planes de financiamiento queda pendiente de definir con contabilidad.</p><form className="form-grid" onSubmit={onCreate}><label className="field"><span>Cliente</span><select name="customer_id" required defaultValue=""><option value="">Selecciona un cliente</option>{customers.map(item=><option key={item.id} value={item.id}>{item.name} · {item.city}</option>)}</select></label><label className="field"><span>Cotización asociada (opcional)</span><select name="quote_id" defaultValue=""><option value="">Sin cotización vinculada</option>{quotes.map(item=><option key={item.id} value={item.id}>{item.folio} · {item.customer?.name || 'Cliente'}</option>)}</select></label><Field label="Vencimiento" name="due_date" type="date" min={today} defaultValue={today} required/><Field label="Importe de la cuota (MXN)" name="amount" type="number" min="0.01" step="0.01" required/><Field label="Número de cuota" name="installment_number" type="number" min="1" step="1" defaultValue={1} required/><label className="field"><span>Forma de pago acordada</span><select name="payment_method" defaultValue="Transferencia"><option>Transferencia</option><option>Efectivo</option><option>Tarjeta</option><option>Otro</option></select></label><div className="modal-actions span-two"><button className="button button-primary" disabled={!customers.length}>Registrar saldo</button></div></form></section>}
    <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">AGENDA DE COBRANZA</span><h2>{filteredReceivables.length} cuotas · {money(openBalance)} de saldo abierto</h2></div><label className="field"><span>Mostrar</span><select value={scheduleFilter} onChange={event=>setScheduleFilter(event.target.value as typeof scheduleFilter)}><option value="all">Todas las fechas</option><option value="overdue">Vencidas</option><option value="today">Vencen hoy</option><option value="upcoming">Próximos 7 días</option><option value="paid">Pagadas</option></select></label></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>VENCIMIENTO / CLIENTE</th><th>COTIZACIÓN / FORMA DE PAGO</th><th>CUOTA</th><th>PAGADO / ABONOS</th><th>SALDO</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{filteredReceivables.map(item=><tr key={item.id}><td>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX')}<small className="sub-cell">{item.customer?.name || 'Cliente'}{item.customer?.phone ? ` · ${item.customer.phone}` : ''}</small></td><td>{item.quote_id ? quotes.find(quote => quote.id === item.quote_id)?.folio || 'Cotización vinculada' : 'Sin cotización'}<small className="sub-cell">{item.payment_method}</small></td><td>{item.installment_number}</td><td>{money(Number(item.paid_amount))}<small className="sub-cell">{(item.payments || []).map(payment => `${new Date(`${payment.paid_on}T12:00:00`).toLocaleDateString('es-MX')} · ${money(Number(payment.amount))} · ${payment.account_name}${payment.is_reversal?' · Corrección':''}${payment.reference ? ` · ${payment.reference}` : ''}`).join(' | ') || 'Sin abonos'}</small></td><td><b>{money(Number(item.balance))}</b></td><td><span className={`status-chip ${item.status === 'paid' ? 'status-approved' : item.status === 'overdue' ? 'status-overdue' : item.status === 'partial' ? 'status-draft' : ''}`}>{item.status === 'paid' ? 'Pagada' : item.status === 'overdue' ? 'Vencida' : item.status === 'partial' ? 'Abono parcial' : 'Pendiente'}</span></td><td><div className="row-actions">{canWrite && item.balance > 0 && <button onClick={() => setPaymentReceivable(item)}>Registrar pago</button>}{canWrite && item.balance > 0 && item.customer?.phone && <button onClick={() => shareReminder(item)}>WhatsApp</button>}{canWrite&&(item.payments||[]).filter(payment=>payment.can_reverse).map(payment=><button key={payment.id} onClick={()=>setCorrectionPayment({receivable:item,payment})}>Corregir {money(Number(payment.amount))}</button>)}</div></td></tr>)}</tbody></table>{!filteredReceivables.length && <EmptyState title="Sin cuotas para esta vista" body={scheduleFilter==='paid'?'Las cuotas pagadas aparecerán aquí.':'No hay pagos pendientes con este vencimiento.'}/>}</div></section>
    {paymentReceivable && <Modal title={`Registrar pago · ${paymentReceivable.customer?.name || 'Cliente'}`} subtitle={`Saldo pendiente: ${money(Number(paymentReceivable.balance))}`} onClose={() => setPaymentReceivable(null)}><form className="form-grid" onSubmit={submitPayment}><Field label="Importe recibido" name="amount" type="number" min="0.01" max={Number(paymentReceivable.balance)} step="0.01" required/><Field label="Fecha de pago" name="paid_on" type="date" defaultValue={today} required/><label className="field span-two"><span>Cuenta que recibió el pago</span><select name="account_id" required defaultValue=""><option value="">Selecciona caja o banco</option>{accounts.map(account=><option key={account.id} value={account.id}>{account.name} · {money(Number(account.current_balance))}</option>)}</select></label><div className="impact-note span-two" role="note"><b>Impacto al aplicar el pago</b><span>Caja/banco: aumenta el importe recibido en la cuenta seleccionada.</span><span>Cliente: el saldo por cobrar de {money(Number(paymentReceivable.balance))} baja por el mismo importe.</span><small>El pago queda ligado a la cuenta por cobrar y al movimiento de caja.</small></div><Field className="span-two" label="Referencia / comprobante (opcional)" name="reference" placeholder="Transferencia, recibo…"/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setPaymentReceivable(null)}>Cancelar</button><button className="button button-primary" disabled={!accounts.length}>Aplicar pago</button></div></form></Modal>}
    {correctionPayment && <Modal title="Corregir pago de cliente" subtitle={`${correctionPayment.receivable.customer?.name || 'Cliente'} · ${money(Number(correctionPayment.payment.amount))}`} onClose={() => setCorrectionPayment(null)}><form className="form-grid" onSubmit={submitPaymentCorrection}><p className="muted-copy span-two">Se agregarán movimientos enlazados para corregir caja y cuenta por cobrar. El pago original no se borra.</p><label className="field span-two"><span>Motivo de la corrección</span><textarea name="reason" minLength={5} maxLength={120} required placeholder="Explica qué dato o movimiento se corrige…"/></label><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setCorrectionPayment(null)}>Cancelar</button><button className="button button-primary">Registrar corrección</button></div></form></Modal>}
  </>;
}

function InventoryView({ items, movements, installations, suppliers, canManage, canIssue, canReadCosts, token, onRefresh, onMovements, onInstallations, announce }: { items: InventoryItem[]; movements: InventoryMovement[]; installations: Installation[]; suppliers: Supplier[]; canManage: boolean; canIssue: boolean; canReadCosts: boolean; token: string; onRefresh: () => Promise<void>; onMovements: (rows: InventoryMovement[]) => void; onInstallations: (rows: Installation[]) => void; announce: (message: string, type?: Notice['type']) => void }) {
  const lowStock = items.filter(item => item.minimum_quantity > 0 && (item.available_quantity ?? item.quantity) <= item.minimum_quantity);
  const [labelItem, setLabelItem] = useState<InventoryItem | null>(null);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const labelCode = labelItem ? (labelItem.barcode || `AE-${labelItem.id}`) : '';
  const [movementItem, setMovementItem] = useState('');
  const [movementFrom, setMovementFrom] = useState('');
  const [movementTo, setMovementTo] = useState('');
  const [movementOffset, setMovementOffset] = useState(movements.length);
  const [hasMoreMovements, setHasMoreMovements] = useState(movements.length >= 500);
  const [loadingMovements, setLoadingMovements] = useState(false);
  const [exportingMovements, setExportingMovements] = useState(false);
  function movementQuery(offset: number) {
    const query = new URLSearchParams({ limit: '500', offset: String(offset) });
    if (movementItem) query.set('item_id', movementItem);
    if (movementFrom) query.set('from_date', movementFrom);
    if (movementTo) query.set('to_date', movementTo);
    return query;
  }
  async function filterMovements(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoadingMovements(true);
    try {
      const rows = await request<InventoryMovement[]>(`/inventory/movements?${movementQuery(0)}`, token);
      onMovements(rows); setMovementOffset(rows.length); setHasMoreMovements(rows.length === 500);
    }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo filtrar el kardex.', 'error'); }
    finally { setLoadingMovements(false); }
  }
  async function loadMoreMovements() {
    setLoadingMovements(true);
    try {
      const rows = await request<InventoryMovement[]>(`/inventory/movements?${movementQuery(movementOffset)}`, token);
      onMovements([...movements, ...rows]); setMovementOffset(current => current + rows.length); setHasMoreMovements(rows.length === 500);
    }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudieron cargar más movimientos.', 'error'); }
    finally { setLoadingMovements(false); }
  }
  async function refreshMovements() {
    setLoadingMovements(true);
    try {
      const rows = await request<InventoryMovement[]>(`/inventory/movements?${movementQuery(0)}`, token);
      onMovements(rows); setMovementOffset(rows.length); setHasMoreMovements(rows.length === 500);
    }
    catch(error) { announce(error instanceof Error ? error.message : 'No se pudo actualizar el kardex.', 'error'); }
    finally { setLoadingMovements(false); }
  }
  async function exportMovements() {
    setExportingMovements(true);
    try {
      const allRows: InventoryMovement[] = [];
      let offset = 0;
      while (true) {
        const page = await request<InventoryMovement[]>(`/inventory/movements?${movementQuery(offset)}`, token);
        allRows.push(...page);
        if (page.length < 500) break;
        offset += page.length;
      }
      if (!allRows.length) { announce('No hay movimientos para exportar.', 'info'); return; }
      const escapeCell = (value: string | number) => {
        let safe = String(value);
        if (typeof value === 'string' && /^[=+\-@\t\r]/.test(safe)) safe = `'${safe}`;
        return `"${safe.replace(/"/g, '""')}"`;
      };
      const headers = ['Fecha', 'Artículo', 'Movimiento', 'Cambio', 'Unidad', ...(canReadCosts ? ['Costo unitario'] : []), 'Referencia', 'Responsable'];
      const rows = allRows.map(row => [new Date(row.created_at).toLocaleString('es-MX'), row.item_name, row.movement_type, row.signed_quantity, row.unit, ...(canReadCosts ? [row.unit_cost ?? ''] : []), row.reason || '', row.created_by]);
      const csv = `\uFEFF${[headers, ...rows].map(row => row.map(escapeCell).join(';')).join('\r\n')}`;
      const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
      const link = document.createElement('a'); link.href = url; link.download = `kardex-${new Date().toISOString().slice(0, 10)}.csv`; link.click(); URL.revokeObjectURL(url);
      announce(`CSV listo: ${allRows.length} movimientos exportados.`);
    } catch(error) { announce(error instanceof Error ? error.message : 'No se pudo exportar el kardex.', 'error'); }
    finally { setExportingMovements(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>, path: string) {
    event.preventDefault(); const form=event.currentTarget; const data=new FormData(form);
    const payload=path.endsWith('/items') ? {name:String(data.get('name')),description:String(data.get('description')||''),category:String(data.get('category')||''),brand:String(data.get('brand')||''),model:String(data.get('model')||''),supplier_id:String(data.get('supplier_id')||'')||null,barcode:String(data.get('barcode')||'')||null,unit:String(data.get('unit')),minimum_quantity:Number(data.get('minimum_quantity')||0),initial_quantity:Number(data.get('initial_quantity')||0),unit_cost:Number(data.get('unit_cost')||0)} : {item_id:String(data.get('item_id')),quantity:Number(data.get('quantity')),unit_cost:Number(data.get('unit_cost')),reason:String(data.get('reason')||'entrada de almacén')};
    try { await request(path, token, {method:'POST',body:JSON.stringify(payload)}); await onRefresh(); const rows=await request<InventoryMovement[]>(`/inventory/movements?${movementQuery(0)}`,token); onMovements(rows); setMovementOffset(rows.length); setHasMoreMovements(rows.length===500); form.reset(); announce(path.endsWith('/items')?'Artículo creado.':'Entrada de almacén registrada.'); } catch(error) { announce(error instanceof Error?error.message:'No se pudo guardar.','error'); }
  }
  async function updateCatalogItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingItem) return;
    const data = new FormData(event.currentTarget);
    const payload = {
      name: String(data.get('name') || ''), description: String(data.get('description') || ''),
      category: String(data.get('category') || ''), brand: String(data.get('brand') || ''),
      model: String(data.get('model') || ''), supplier_id: String(data.get('supplier_id') || '') || null,
      barcode: String(data.get('barcode') || '') || null, unit: String(data.get('unit') || ''),
      minimum_quantity: Number(data.get('minimum_quantity') || 0), unit_cost: Number(data.get('unit_cost') || 0),
    };
    try {
      await request(`/inventory/items/${encodeURIComponent(editingItem.id)}`, token, { method: 'PUT', body: JSON.stringify(payload) });
      await onRefresh();
      setEditingItem(null);
      announce('Ficha del material actualizada. Las existencias se mantienen sin cambios.');
    } catch (error) { announce(error instanceof Error ? error.message : 'No se pudo actualizar el material.', 'error'); }
  }
  async function reloadAfterIssue() {
    await onRefresh();
    const [movementRows, orderRows] = await Promise.all([
      request<InventoryMovement[]>(`/inventory/movements?${movementQuery(0)}`, token),
      request<Installation[]>('/installations', token),
    ]);
    onMovements(movementRows); onInstallations(orderRows);
  }
  return <>{canIssue&&<InventoryIssueIntake installations={installations} movements={movements} token={token} onSaved={reloadAfterIssue} announce={announce}/>}<div className="dashboard-grid"><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">ALMACÉN</span><h2>{items.length} artículos</h2></div><span className={`status-chip ${lowStock.length ? 'status-overdue' : 'status-approved'}`}>{lowStock.length ? `${lowStock.length} por reabastecer` : 'Existencias al día'}</span></div>{lowStock.length>0&&<div className="notice warning"><b>Stock bajo</b><span>{lowStock.map(item=>`${item.name}: ${item.available_quantity ?? item.quantity} disponibles ${item.unit} (mínimo ${item.minimum_quantity})`).join(' · ')}</span></div>}{canManage&&<div className="dashboard-grid"><form className="team-form" onSubmit={event=>void submit(event,'/inventory/items')}><h3>Nuevo artículo</h3><Field label="Nombre del material" name="name" required placeholder="Ej. Panel fotovoltaico"/><label className="field"><span>Descripción</span><textarea name="description" maxLength={1000} placeholder="Características y especificaciones"/></label><Field label="Categoría" name="category" placeholder="Módulos, estructura, inversores"/><Field label="Marca" name="brand" placeholder="Fabricante"/><Field label="Modelo" name="model" placeholder="Clave de modelo"/><label className="field"><span>Proveedor habitual</span><select name="supplier_id"><option value="">Sin proveedor asignado</option>{suppliers.filter(item=>item.active).map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Código QR / barras" name="barcode" maxLength={120} placeholder="Escanea o captura el código"/><Field label="Unidad" name="unit" required defaultValue="pieza" placeholder="pieza, metro, par"/><Field label="Existencia inicial" name="initial_quantity" type="number" min="0" step="0.01" defaultValue={0}/><Field label="Mínimo de alerta" name="minimum_quantity" type="number" min="0" step="0.01" defaultValue={0}/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" defaultValue={0}/><button className="button button-primary">Agregar artículo</button></form><form className="team-form" onSubmit={event=>void submit(event,'/inventory/receive')}><h3>Entrada de almacén</h3><label className="field"><span>Artículo</span><select name="item_id" required><option value="">Selecciona material</option>{items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Cantidad recibida" name="quantity" type="number" min="0.01" step="0.01" required/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" required/><Field label="Referencia" name="reason" placeholder="Factura, proveedor o nota"/><button className="button button-primary">Registrar entrada</button></form></div>}<div className="data-table-wrap"><table className="data-table"><thead><tr><th>ARTÍCULO</th><th>EXISTENCIA</th><th>MÍNIMO</th>{canReadCosts&&<th>COSTO UNITARIO</th>}</tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.name}<small className="sub-cell">{[item.category,item.brand,item.model].filter(Boolean).join(" · ") || item.description || item.unit}</small>{item.supplier_id&&<small className="sub-cell">Proveedor: {suppliers.find(supplier=>supplier.id===item.supplier_id)?.name||"sin nombre"}</small>}{item.barcode&&<small className="sub-cell">Código: {item.barcode}</small>}{canManage&&<div className="inventory-item-actions"><button type="button" className="text-action inventory-label-action" onClick={()=>setEditingItem(item)}>Editar ficha</button><button type="button" className="text-action inventory-label-action" onClick={()=>setLabelItem(item)}>Imprimir QR</button></div>}</td><td>{item.available_quantity ?? item.quantity} {item.unit}<small className="sub-cell">{item.reserved_quantity ? `${item.reserved_quantity} asignados a órdenes` : `${item.quantity} físicos`}</small></td><td>{item.minimum_quantity}</td>{canReadCosts&&<td>{money(item.unit_cost)}</td>}</tr>)}</tbody></table>{!items.length&&<EmptyState title="Almacén sin artículos" body="Crea el catálogo de materiales reales para empezar a registrar existencias."/>}</div></section><section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">KARDEX · {movements.length} MOVIMIENTOS CARGADOS</span><h2>Historial de almacén</h2></div><div className="heading-actions"><button className="button button-outline" disabled={loadingMovements} onClick={()=>void refreshMovements()}>{loadingMovements?'Actualizando…':'Actualizar'}</button><button className="button button-outline" disabled={exportingMovements} onClick={()=>void exportMovements()}>{exportingMovements?'Exportando todo…':'Descargar CSV completo'}</button></div></div><form className="kardex-filter" onSubmit={event=>void filterMovements(event)}><label>Artículo<select value={movementItem} onChange={event=>setMovementItem(event.target.value)}><option value="">Todos los artículos</option>{items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Desde<input type="date" value={movementFrom} onChange={event=>setMovementFrom(event.target.value)}/></label><label>Hasta<input type="date" value={movementTo} onChange={event=>setMovementTo(event.target.value)}/></label><button className="button button-outline" disabled={loadingMovements}>{loadingMovements?'Consultando…':'Filtrar'}</button></form><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>ARTÍCULO</th><th>MOVIMIENTO</th><th>CAMBIO</th>{canReadCosts&&<th>COSTO UNITARIO</th>}<th>REFERENCIA</th></tr></thead><tbody>{movements.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-MX')}</td><td>{row.item_name}<small className="sub-cell">{row.created_by}</small></td><td>{row.movement_type==='out'?'Salida':row.movement_type==='consumption'?'Consumo confirmado':row.movement_type==='consumption_return'?'Consumo corregido':row.movement_type==='waste'?'Merma':row.movement_type==='return'?'Devolución':row.movement_type==='damage'?'Merma por daño':'Entrada'}</td><td>{row.signed_quantity>0?'+':''}{row.signed_quantity} {row.unit}</td>{canReadCosts&&<td>{row.unit_cost===null||row.unit_cost===undefined?'Sin dato':money(row.unit_cost)}</td>}<td>{row.reason||'—'}</td></tr>)}</tbody></table>{!movements.length&&<EmptyState title="Sin movimientos registrados" body="Las entradas y consumos aparecerán aquí con fecha, responsable y referencia."/>}</div>{hasMoreMovements&&<div className="table-pagination"><span>Mostrando {movements.length} movimientos; hay más por cargar.</span><button className="button button-outline" onClick={()=>void loadMoreMovements()} disabled={loadingMovements}>{loadingMovements?'Cargando…':'Cargar siguientes 500'}</button></div>}</section></div>{editingItem&&<Modal title="Editar material" subtitle="Corrige la ficha del catálogo; el saldo físico solo cambia mediante movimientos de almacén." onClose={()=>setEditingItem(null)} wide><form className="form-grid" onSubmit={event=>void updateCatalogItem(event)}><Field label="Nombre del material" name="name" required defaultValue={editingItem.name}/><Field label="Unidad" name="unit" required defaultValue={editingItem.unit}/><label className="field span-two"><span>Descripción</span><textarea name="description" maxLength={1000} defaultValue={editingItem.description||""}/></label><Field label="Categoría" name="category" defaultValue={editingItem.category||""}/><Field label="Marca" name="brand" defaultValue={editingItem.brand||""}/><Field label="Modelo" name="model" defaultValue={editingItem.model||""}/><label className="field"><span>Proveedor habitual</span><select name="supplier_id" defaultValue={editingItem.supplier_id||""}><option value="">Sin proveedor asignado</option>{suppliers.filter(item=>item.active).map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><Field label="Código QR / barras" name="barcode" maxLength={120} defaultValue={editingItem.barcode||""}/><Field label="Mínimo de alerta" name="minimum_quantity" type="number" min="0" step="0.01" defaultValue={editingItem.minimum_quantity}/><Field label="Costo unitario (MXN)" name="unit_cost" type="number" min="0" step="0.01" defaultValue={editingItem.unit_cost}/><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={()=>setEditingItem(null)}>Cancelar</button><button className="button button-primary">Guardar cambios</button></div></form></Modal>}{labelItem&&<div className="inventory-label-overlay"><section className="inventory-label-card"><button className="inventory-label-close" onClick={()=>setLabelItem(null)} aria-label="Cerrar etiqueta">×</button><QRCodeSVG value={labelCode} size={220} level="M" includeMargin/><h2>{labelItem.name}</h2><p>{labelItem.category||labelItem.brand||"Artículo de ArcoEnergy"}</p><code>{labelCode}</code><div className="inventory-label-actions"><button className="button button-outline" onClick={()=>window.print()}>Imprimir etiqueta</button><button className="button button-primary" onClick={()=>setLabelItem(null)}>Cerrar</button></div></section></div>}</>;
}

function ProfitabilityView({ token }: { token: string }) {
  const now = new Date();
  const [month, setMonth] = useState(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
  const [report, setReport] = useState<ProfitabilityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) return;
    let active = true;
    setLoading(true); setError('');
    request<ProfitabilityReport>(`/reports/profitability?month=${encodeURIComponent(month)}`, token)
      .then(result => { if (active) setReport(result); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'No se pudo cargar el reporte.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token, month, refreshKey]);

  return <div className="dashboard-grid">
    <section className="surface-card table-surface">
      <div className="table-toolbar"><div><span className="eyebrow">RESULTADO OPERATIVO PRELIMINAR</span><h2>Por proyecto y mes</h2></div><button className="button button-outline" onClick={() => setRefreshKey(value => value + 1)} disabled={loading}>{loading ? 'Actualizando…' : 'Actualizar'}</button></div>
      <form className="kardex-filter" onSubmit={event => { event.preventDefault(); setRefreshKey(value => value + 1); }}><label>Periodo<input type="month" value={month} onChange={event => setMonth(event.target.value)} required/></label><button className="button button-primary" disabled={loading}>Consultar</button></form>
      {error && <p role="alert" className="error-message">{error}</p>}
      {report && <>
        <div className="notice warning"><b>Reporte preliminar</b><span>Incluye ventas registradas − costo de material consumido − gastos capturados. Devoluciones de venta y bonificaciones aún no se registran; no es un estado contable formal.</span></div>
        <p className="muted-copy">{report.basis} · {report.totals.missing_cost_movements ? `${report.totals.missing_cost_movements} consumos sin costo unitario` : 'Todos los consumos del periodo tienen costo unitario registrado.'}</p>
        <section className="stats"><article><small>VENTAS REGISTRADAS</small><strong>{money(report.totals.sales)}</strong><span>Fecha de registro de venta</span></article><article><small>COSTO DE MATERIAL CONSUMIDO</small><strong>{report.totals.materials_cost === null ? 'Sin costo completo' : money(report.totals.materials_cost)}</strong><span>Por fecha de confirmación</span></article><article><small>GASTOS CAPTURADOS</small><strong>{money(report.totals.expenses)}</strong><span>Por fecha capturada</span></article><article><small>RESULTADO PRELIMINAR</small><strong>{report.totals.preliminary_result === null ? 'Incompleto' : money(report.totals.preliminary_result)}</strong><span>Antes de devoluciones y bonificaciones</span></article></section>
        <div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROYECTO / ORDEN</th><th>CIUDAD</th><th>VENTAS</th><th>COSTO MATERIAL</th><th>GASTOS</th><th>RESULTADO PRELIMINAR</th></tr></thead><tbody>{report.rows.map(row => <tr key={row.installation_id || 'unassigned'}><td>{row.project}<small className="sub-cell">{row.folio || 'Sin orden de trabajo'}</small></td><td>{row.city || '—'}</td><td>{money(row.sales)}</td><td>{row.materials_cost === null ? 'Costo pendiente' : money(row.materials_cost)}{row.missing_cost_movements > 0 && <small className="sub-cell">{row.missing_cost_movements} movimientos sin costo</small>}</td><td>{money(row.expenses)}<small className="sub-cell">{Object.entries(row.expenses_by_category).map(([category, amount]) => `${category}: ${money(amount)}`).join(' · ')}</small></td><td><b>{row.preliminary_result === null ? 'Incompleto' : money(row.preliminary_result)}</b></td></tr>)}</tbody></table>{report.rows.length === 0 && <EmptyState title="Sin movimientos en el periodo" body="El reporte aparecerá cuando haya ventas, consumo de materiales o gastos reales en el mes seleccionado."/>}</div>
      </>}
    </section>
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

function InstallationsView({ items, customers, team, canWrite, token, onRefresh, announce }: { items: Installation[]; customers: Customer[]; team: TeamMember[]; canWrite: boolean; token: string; onRefresh: () => Promise<void>; announce: (message: string, type?: Notice['type']) => void }) {
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const date = String(form.get('scheduled_at') || '');
    const assignedInstallers = form.getAll('assigned_installers').map(String);
    const payload = { customer_id: String(form.get('customer_id') || ''), lead_installer: assignedInstallers[0] || '', assigned_installers: assignedInstallers, scheduled_at: date ? new Date(date).toISOString() : null, notes: String(form.get('notes') || '') };
    try { await request('/installations', token, { method: 'POST', body: JSON.stringify(payload) }); await onRefresh(); event.currentTarget.reset(); announce('Orden asignada al instalador.'); }
    catch (error) { announce(error instanceof Error ? error.message : 'No se pudo crear la orden.', 'error'); }
  }
  return <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">COORDINACIÓN DE CAMPO</span><h2>{items.length} órdenes de trabajo</h2></div></div>{canWrite && <form className="team-form" onSubmit={create}><label className="field"><span>Cliente / proyecto</span><select name="customer_id" required><option value="">Selecciona cliente</option>{customers.map(customer=><option key={customer.id} value={customer.id}>{customer.name} · {customer.city}</option>)}</select></label><label className="field"><span>Cuadrilla instaladora</span><select name="assigned_installers" multiple required size={Math.min(5, Math.max(2, team.filter(member=>member.roles.includes('instalador')).length))}>{team.filter(member=>member.roles.includes('instalador')).map(member=><option key={member.id} value={member.email}>{member.name} · {member.email}</option>)}</select><small>Selecciona una o más cuentas instaladoras; la primera será responsable.</small></label><Field label="Fecha y hora" name="scheduled_at" type="datetime-local"/><Field label="Instrucciones" name="notes" placeholder="Alcance y detalles de la orden"/><button className="button button-primary">Asignar orden de trabajo</button></form>}{items.length ? <div className="data-table-wrap"><table className="data-table"><thead><tr><th>PROYECTO</th><th>CLIENTE</th><th>CONTACTO</th><th>INSTALADOR</th><th>FECHA</th><th>ESTADO</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.quote_id||'Proyecto'}</td><td>{item.customer?.name||'Cliente'}<small className="sub-cell">{item.customer?.city}</small></td><td>{item.customer?.phone||'—'}<small className="sub-cell">{item.customer?.email||''}</small></td><td>{(item.assigned_installers||[item.lead_installer]).join(', ')}<small className="sub-cell">{item.confirmed_installers?.length||0}/{item.assigned_installers?.length||1} confirmadas</small></td><td>{item.scheduled_at?new Date(item.scheduled_at).toLocaleString('es-MX'):'Por programar'}</td><td>{item.status}</td></tr>)}</tbody></table></div>:<EmptyState title="Sin órdenes de trabajo" body="Las asignaciones aparecerán aquí y en la PWA del instalador."/>}</section>;
}

function CatalogView({ catalog, onSave, onLogin }: { catalog: CatalogPayload | null; onSave: (event: FormEvent<HTMLFormElement>, item: Package) => Promise<boolean>; onLogin: () => void }) {
  const [editingPackage, setEditingPackage] = useState<Package | null>(null);
  const [newCount, setNewCount] = useState(4);
  const beginNewPackage = () => { if (items.some(item => item.panel_count === newCount)) { setEditingPackage(items.find(item => item.panel_count === newCount)!); return; } setEditingPackage({ id: '', panel_count: newCount, panel_brand: '', panel_watts: 0, panel_unit_price: 0, structure_name: '', structure_price: 0, inverter_options: [], default_inverter: '', payment_methods: ['Contado'], enabled: true, pricing_approved: false, price_mxn: 0, system_kw: 0 }); };
  const items = catalog?.packages || [];
  return <><div className="catalog-summary"><div><span className="eyebrow">CONFIGURACIÓN COMERCIAL</span><h2>Paquetes de 4 a 20 paneles</h2><p>{catalog?.catalog_note || 'Configura el catálogo de cotización.'}</p></div><div className="toolbar-actions"><select aria-label="Cantidad de paneles del paquete" value={newCount} onChange={event => setNewCount(Number(event.target.value))}>{Array.from({length:17},(_,i)=>i+4).map(count=><option key={count} value={count}>{count} paneles</option>)}</select><button className="button button-primary" onClick={beginNewPackage}>＋ Agregar paquete</button></div></div><section className="package-grid">{items.map(item => <article className="package-card" key={item.panel_count}><div className="package-head"><span className="package-count">{item.panel_count}<small>paneles</small></span><span className={`status-chip ${item.pricing_approved ? 'status-overdue' : 'status-approved'}`}>{item.pricing_approved ? 'Pendiente de aprobación' : 'Aprobado'}</span></div><h3>{item.panel_brand} {item.panel_watts} W</h3><p>{item.system_kw.toFixed(1)} kWp · {item.default_inverter || 'Inversor pendiente'}</p><div className="package-price">{money(item.price_mxn)}<small>{item.enabled ? 'precio de paquete' : 'desactivado'}</small></div><button className="button button-outline" onClick={() => setEditingPackage(item)}>Editar paquete</button></article>)}</section>{!items.length && <EmptyState title="No hay paquetes configurados" body="Agrega los equipos y precios vigentes aprobados por Arco Energy." action="Configurar paquete" onClick={beginNewPackage}/>}
    {editingPackage && <Modal title={`${editingPackage.panel_count} paneles`} subtitle="Edita valores y marca si están aprobados para cotizar con clientes." onClose={() => setEditingPackage(null)} wide><form className="form-grid" onSubmit={async event => { if (await onSave(event, editingPackage)) setEditingPackage(null); }}><Field label="Marca de panel" name="panel_brand" required defaultValue={editingPackage.panel_brand}/><Field label="Potencia por panel (W)" name="panel_watts" type="number" min="100" max="1000" required defaultValue={editingPackage.panel_watts}/><Field label="Precio por panel (MXN)" name="panel_unit_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.panel_unit_price}/><Field label="Nombre de estructura" name="structure_name" required defaultValue={editingPackage.structure_name}/><Field label="Precio de estructura (MXN)" name="structure_price" type="number" min="0" step="0.01" required defaultValue={editingPackage.structure_price}/><label className="field span-two">Inversores disponibles <small>Un inversor por línea: Nombre | Precio MXN</small><textarea name="inverters" required defaultValue={editingPackage.inverter_options.map(item => `${item.name} | ${item.price_mxn}`).join('\n')}/></label><Field label="Inversor predeterminado" name="default_inverter" required defaultValue={editingPackage.default_inverter}/><div className="field"><span>Formas de pago</span><div className="check-list">{['Contado', 'Financiamiento', 'Plan 24'].map(method => <label key={method}><input type="checkbox" name="payment_method" value={method} defaultChecked={editingPackage.payment_methods.includes(method)}/>{method}</label>)}</div></div><label className="check-confirm span-two"><input type="checkbox" name="enabled" defaultChecked={editingPackage.enabled}/> Paquete disponible para nuevas cotizaciones</label><label className="approval-confirm span-two"><input type="checkbox" name="approved_prices"/> Confirmo que estos precios y equipos fueron revisados y aprobados por Arco Energy.</label><div className="modal-actions span-two"><button type="button" className="button button-outline" onClick={() => setEditingPackage(null)}>Cancelar</button><button className="button button-primary">Guardar paquete</button></div></form></Modal>}
  </>;
}

function TeamView({ members, roleDefinitions, loading, error, name, email, password, role, busy, onName, onEmail, onPassword, onRole, onSubmit, onUpdateRole }: { members: TeamMember[]; roleDefinitions: RoleDefinition[]; loading: boolean; error: string; name: string; email: string; password: string; role: string; busy: boolean; onName: (v: string) => void; onEmail: (v: string) => void; onPassword: (v: string) => void; onRole: (v: string) => void; onSubmit: (e: FormEvent<HTMLFormElement>) => void; onUpdateRole: (id: string, role: string) => void }) {
  return <><section className="surface-card team-surface"><div className="section-title"><div><span className="eyebrow">CUENTAS Y PERMISOS</span><h2>Personas en el equipo</h2></div><span className="status-chip status-approved">5 roles</span></div><p className="muted-copy">Los permisos se validan en la API además de controlar qué se muestra en cada pantalla.</p><form className="team-form" onSubmit={onSubmit}><Field label="Nombre" value={name} onChange={onName} required placeholder="Nombre completo"/><Field label="Correo" type="email" value={email} onChange={onEmail} required placeholder="persona@arcoenergy.mx"/><Field label="Contraseña temporal" type="password" value={password} onChange={onPassword} required minLength={12} placeholder="12 caracteres mínimo"/><label className="field"><span>Rol</span><select value={role} onChange={event => onRole(event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button className="button button-primary" disabled={busy}>{busy ? 'Creando…' : '＋ Crear usuario'}</button></form>{error && <p className="error-message">{error}</p>}{loading && <p className="muted-copy">Cargando equipo y permisos…</p>}<div className="team-list">{members.map(member => <div className="team-row" key={member.id}><span className="avatar-soft">{initials(member.name)}</span><div><b>{member.name}</b><small>{member.email}</small></div><select aria-label={`Rol de ${member.name}`} value={member.roles[0] || ''} onChange={event => onUpdateRole(member.id, event.target.value)}>{roleOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>)}</div></section><section className="surface-card role-matrix"><div className="section-title"><div><span className="eyebrow">MATRIZ DE ACCESO</span><h2>Qué puede hacer cada rol</h2></div></div><p className="muted-copy">Permisos configurados en la API. Son asignaciones predefinidas; el CRM no permite añadir permisos individuales.</p>{roleDefinitions.length ? <div className="role-matrix-grid">{roleDefinitions.map(definition => <article className="role-permission-card" key={definition.id}><h3>{definition.label}</h3><ul>{definition.permissions.map(permission => <li key={permission}>{permissionLabel[permission] || permission}</li>)}</ul></article>)}</div> : <p className="muted-copy">{loading ? 'Cargando matriz…' : 'No fue posible cargar la matriz de permisos.'}</p>}</section></>;
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
  const defaultDate = new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10);
  const [followupDays, setFollowupDays] = useState('3');
  const [followupDate, setFollowupDate] = useState(defaultDate);
  function selectFollowup(value: string) { setFollowupDays(value); if (value !== 'custom') setFollowupDate(new Date(Date.now() + Number(value) * 86400000).toISOString().slice(0, 10)); }
  return <div className="drawer-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><aside className="customer-drawer"><header><div><span className="eyebrow">FICHA DE CLIENTE</span><button className="drawer-close" onClick={onClose}>×</button></div><div className="drawer-profile"><span className="profile-avatar">{initials(customer.name)}</span><div><h2>{customer.name}</h2><small>{customer.city} · {labelCustomerStatus(customer.status)}</small></div></div><div className="contact-actions"><a href={customer.phone ? `tel:${customer.phone}` : undefined} aria-disabled={!customer.phone}>☎ Llamar</a><a className="wa-action" target="_blank" rel="noreferrer" href={customer.phone ? `https://wa.me/${customer.phone.replace(/\D/g, '')}` : undefined}>◉ WhatsApp</a></div><div className="contact-block"><b>Datos de contacto</b><span>{customer.phone || 'Teléfono pendiente'}</span><span>{customer.email || 'Correo pendiente'}</span><span>{customer.address || customer.city || 'Ubicación pendiente'}</span></div></header><div className="drawer-body"><section><div className="section-title"><div><span className="eyebrow">PROPUESTAS</span><h3>{quotes.length} cotizaciones</h3></div></div>{quotes.length ? quotes.map(item => <div className="drawer-quote" key={item.id}><div><b>{item.folio}</b><small>{item.panel_count} paneles · {item.status}</small></div><strong>{money(item.total)}</strong><button className="icon-button" onClick={() => onDownload(item)}>PDF</button></div>) : <p className="empty-inline">Sin cotizaciones todavía.</p>}</section><section><div className="section-title"><div><span className="eyebrow">PRÓXIMO CONTACTO</span><h3>{followups.length} seguimientos</h3></div></div>{followups.map(item => <div className="drawer-followup" key={item.id}><b>{new Date(`${item.due_date}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}</b><span>{item.note}</span><small>Responsable: {item.assigned_to || 'pendiente'}</small></div>)}</section>{canWrite && <section className="note-box"><div className="note-tabs"><button className={mode === 'nota' ? 'active' : ''} onClick={() => setMode('nota')}>Agregar nota</button><button className={mode === 'seguimiento' ? 'active' : ''} onClick={() => setMode('seguimiento')}>Programar seguimiento</button></div>{mode === 'nota' ? <form onSubmit={onAddActivity}><textarea name="note" required maxLength={5000} placeholder="Escribe una nota para la bitácora…"/><button className="button button-primary">Guardar nota</button></form> : <form onSubmit={onSchedule}><label className="field"><span>Cuándo volver a contactar</span><select value={followupDays} onChange={event => selectFollowup(event.target.value)}><option value="3">En 3 días</option><option value="7">En 7 días</option><option value="15">En 15 días</option><option value="30">En 30 días</option><option value="custom">Elegir fecha</option></select></label><label className="field"><span>Fecha para contactar</span><input name="due_date" type="date" min={new Date().toISOString().slice(0, 10)} value={followupDate} onChange={event => { setFollowupDate(event.target.value); setFollowupDays("custom"); }} required/></label><label className="field"><span>Motivo / comentario del cliente</span><textarea name="note" required placeholder="¿Qué comentó y qué hay que retomar?"/></label>{canAssign && <label className="field"><span>Persona responsable</span><select name="assigned_to" defaultValue={currentEmail.toLowerCase()} required><option value={currentEmail.toLowerCase()}>Yo · {currentEmail}</option>{team.filter(member => member.email.toLowerCase() !== currentEmail.toLowerCase()).map(member => <option key={member.id} value={member.email.toLowerCase()}>{member.name} · {member.email}</option>)}</select></label>}<button className="button button-primary">Programar contacto</button></form>}</section>}<section><div className="section-title"><div><span className="eyebrow">BITÁCORA</span><h3>Actividad reciente</h3></div></div>{activities.length ? activities.map(item => <div className="activity-row" key={item.id}><i/><div><b>{item.kind}</b><p>{item.note}</p><small>{item.created_by || 'Equipo'} · {new Date(item.created_at).toLocaleString('es-MX')}</small></div></div>) : <p className="empty-inline">Aún no hay actividad registrada.</p>}</section></div><footer className="drawer-foot">{`Origen: ${customer.source === 'public_web' ? 'Web pública' : 'Equipo Arco Energy'}`}</footer></aside></div>;
}

function Metric({ label, value, note, icon, tone }: { label: string; value: string; note: string; icon: string; tone: string }) { return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className={`metric-icon tone-${tone}`}>{icon}</i></div><strong>{value}</strong><small>{note}</small></article>; }
function EmptyState({ title, body, action, onClick }: { title: string; body: string; action?: string; onClick?: () => void }) { return <div className="empty-state"><span>✦</span><h3>{title}</h3><p>{body}</p>{action && onClick && <button className="button button-outline" onClick={onClick}>{action}</button>}</div>; }
function Modal({ title, subtitle, onClose, wide = false, children }: { title: string; subtitle: string; onClose: () => void; wide?: boolean; children: ReactNode }) { return <div className="modal-scrim" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className={`modal-card ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><header className="modal-header"><div><span className="eyebrow">ARCO ENERGY</span><h2>{title}</h2><p>{subtitle}</p></div><button className="drawer-close" onClick={onClose} aria-label="Cerrar">×</button></header><div className="modal-body">{children}</div></section></div>; }
function Field({ label, name, type = 'text', required = false, placeholder, defaultValue, value, onChange, className = '', min, max, step, minLength, maxLength }: { label: string; name?: string; type?: string; required?: boolean; placeholder?: string; defaultValue?: string | number; value?: string; onChange?: (value: string) => void; className?: string; min?: string | number; max?: string | number; step?: string | number; minLength?: number; maxLength?: number }) { return <label className={`field ${className}`}><span>{label}</span><input name={name} type={type} required={required} placeholder={placeholder} defaultValue={value === undefined ? defaultValue : undefined} value={value} onChange={event => onChange?.(event.target.value)} min={min} max={max} step={step} minLength={minLength} maxLength={maxLength}/></label>; }
function labelStatus(status: string) { return ({ draft: 'Borrador', sent: 'Enviada', accepted: 'Aceptada', declined: 'No aceptada', overdue: 'Vencido' })[status] || status; }
function labelCustomerStatus(status: string) { return ({ lead: 'Prospecto', qualified: 'En conversación', followup: 'Seguimiento', customer: 'Cliente' })[status] || status; }
function LoginScreen() { const { login, loading, error } = useAuth(); const [failure, setFailure] = useState(''); return <div className="login-screen"><a className="crm-brand" href="/"><span className="brand-mark">A</span><span>arco<span>energy</span><small>GESTIÓN SOLAR</small></span></a><section className="login-card"><span className="eyebrow">ACCESO DE EQUIPO</span><h1>Iniciar sesión</h1><p>Ingresa con la cuenta de tu negocio.</p><form onSubmit={async event => { event.preventDefault(); const form = new FormData(event.currentTarget); setFailure(''); try { await login(String(form.get('email')), String(form.get('password')), form.get('remember') === 'on'); window.location.replace('/crm/'); } catch (err) { setFailure(err instanceof Error ? err.message : error || 'No se pudo iniciar sesión.'); } }}><Field label="Correo electrónico" name="email" type="email" required/><Field label="Contraseña" name="password" type="password" required/><label className="field"><span><input type="checkbox" name="remember" defaultChecked/> Mantener sesión iniciada</span></label>{failure && <p role="alert">{failure}</p>}<button className="button button-primary" disabled={loading}>{loading ? 'Iniciando…' : 'Entrar'}</button></form><a href="/app/login">Acceso móvil</a></section></div>; }
