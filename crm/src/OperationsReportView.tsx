import { useEffect, useState, type FormEvent } from 'react';

type OperationsReport = {
  basis: string;
  stock: { items:Array<{id:string;name:string;category:string;unit:string;quantity:number;reserved_quantity:number;available_quantity:number;minimum_quantity:number;low_stock:boolean;unit_cost?:number}>; item_count:number; low_stock_count:number; estimated_value:number|null };
  movements: { items:Array<{id:string;created_at:string;item_name:string;unit:string;movement_type:string;quantity:number;installation_folio:string|null;reason:string;created_by:string;unit_cost?:number|null}>; truncated:boolean; totals_by_type:Array<{movement_type:string;quantity:number}> };
  customers_by_status:Array<{status:string;count:number}>;
  suppliers:{total:number;active:number;inactive:number};
  installations_by_status:Array<{status:string;count:number}>;
  expenses:{total:number;by_category:Array<{category:string;amount:number}>;count:number};
  cash_flow:null|{from_date:string|null;to_date:string|null;opening_balance:number;opening_entries:number;inflows:number;outflows:number;closing_balance:number;basis:string;accounts:Array<{id:string;name:string;account_type:string;opening_balance:number;opening_entries:number;inflows:number;outflows:number;closing_balance:number}>};
};

const money = (amount:number) => new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:2}).format(amount);
const statusNames:Record<string,string> = {lead:'Prospecto',active:'Activo',qualified:'Calificado',assigned:'Asignada',scheduled:'Programada',in_progress:'En curso',closed:'Cerrada',cancelled:'Cancelada'};
const movementNames:Record<string,string> = {in:'Entrada',out:'Salida',return:'Devolución',waste:'Merma',consumption:'Consumo confirmado',consumption_return:'Consumo corregido'};
const stockColors = ['#4b9870','#d78a38','#c65c51'];

export function OperationsReportView({token}:{token:string}) {
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  const [fromDate,setFromDate] = useState(`${today.slice(0,7)}-01`);
  const [toDate,setToDate] = useState(today);
  const [range,setRange] = useState({from:`${today.slice(0,7)}-01`,to:today});
  const [report,setReport] = useState<OperationsReport|null>(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(false);

  useEffect(()=>{
    let active=true;
    setLoading(true); setError('');
    const params=new URLSearchParams({from_date:range.from,to_date:range.to});
    void fetch(`/api/v1/reports/operations?${params}`,{headers:{Authorization:`Bearer ${token}`}})
      .then(async response=>{if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||'No se pudo cargar el reporte operativo.');}return response.json();})
      .then((data:OperationsReport)=>{if(active)setReport(data);})
      .catch(reason=>{if(active)setError(reason instanceof Error?reason.message:'No se pudo cargar el reporte operativo.');})
      .finally(()=>{if(active)setLoading(false);});
    return ()=>{active=false;};
  },[token,range]);

  function applyFilters(event:FormEvent<HTMLFormElement>){event.preventDefault();setRange({from:fromDate,to:toDate});}
  function exportMovements(){
    if(!report?.movements.items.length)return;
    const includeCost=report.movements.items.some(row=>row.unit_cost!==undefined);
    const headers=['Fecha','Artículo','Movimiento','Cantidad','Unidad','Orden','Referencia','Responsable',...(includeCost?['Costo unitario']:[])];
    const escape=(value:unknown)=>{let cell=String(value??'');if(/^[=+\-@\t\r]/.test(cell))cell=`'${cell}`;return `"${cell.replace(/"/g,'""')}"`;};
    const rows=report.movements.items.map(row=>[new Date(row.created_at).toLocaleString('es-MX'),row.item_name,row.movement_type,row.quantity,row.unit,row.installation_folio||'',row.reason,row.created_by,...(includeCost?[row.unit_cost??'']:[])]);
    const file=URL.createObjectURL(new Blob([`\uFEFF${[headers,...rows].map(row=>row.map(escape).join(';')).join('\r\n')}`],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=file;link.download=`arcoenergy-operacion-${range.from}-${range.to}.csv`;link.click();URL.revokeObjectURL(file);
  }

  const maxExpense=Math.max(1,...(report?.expenses.by_category.map(item=>Number(item.amount))||[]));
  const stockStatusCounts = report?.stock.items.reduce((counts,item)=>{
    const available=Number(item.available_quantity);
    if(available<=0)counts.depleted+=1;
    else if(Number(item.minimum_quantity)>0&&available<=Number(item.minimum_quantity))counts.low+=1;
    else counts.available+=1;
    return counts;
  },{available:0,low:0,depleted:0})||{available:0,low:0,depleted:0};
  const stockStatusRows=[{label:'Disponible',count:stockStatusCounts.available,color:stockColors[0]},{label:'Stock bajo',count:stockStatusCounts.low,color:stockColors[1]},{label:'Agotado',count:stockStatusCounts.depleted,color:stockColors[2]}];
  const stockStatusTotal=stockStatusRows.reduce((sum,row)=>sum+row.count,0);
  let stockChartEnd=0;
  const stockChartStops=stockStatusRows.map(row=>{
    const start=stockChartEnd;
    stockChartEnd+=stockStatusTotal?row.count/stockStatusTotal*100:0;
    return `${row.color} ${start}% ${stockChartEnd}%`;
  }).join(',');
  const statusRows=(rows:Array<{status:string;count:number}>)=>rows.length?<div className="operations-status-list">{rows.map(row=><div key={row.status}><span>{statusNames[row.status]||row.status}</span><b>{row.count}</b></div>)}</div>:<p className="muted-copy">Sin registros.</p>;
  return <div className="operations-report">
    <section className="surface-card operations-report-filter"><div><span className="eyebrow">REPORTES OPERATIVOS</span><h2>Existencias y actividad</h2></div><form onSubmit={applyFilters}><label>Desde<input type="date" value={fromDate} onChange={event=>setFromDate(event.target.value)} required/></label><label>Hasta<input type="date" value={toDate} onChange={event=>setToDate(event.target.value)} required/></label><button className="button button-primary" disabled={loading}>{loading?'Actualizando…':'Consultar'}</button></form></section>
    <p className="operations-report-basis">{report?.basis||'El reporte distingue existencias actuales de actividad registrada en el periodo seleccionado.'}</p>
    {error&&<p role="alert" className="error-message">{error}</p>}
    {report&&<>
      <section className="metric-grid"><OperationsMetric label="ARTÍCULOS" value={String(report.stock.item_count)} icon="▦"/><OperationsMetric label="STOCK BAJO" value={String(report.stock.low_stock_count)} icon="!"/><OperationsMetric label="MOVIMIENTOS" value={String(report.movements.items.length)} icon="↕"/><OperationsMetric label="GASTOS CAPTURADOS" value={money(report.expenses.total)} icon="$"/></section>
      {report.cash_flow&&<section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">FLUJO DE CAJA · CUENTAS ACTIVAS</span><h2>Dinero registrado en el periodo</h2></div><span className="status-chip status-approved">{range.from} — {range.to}</span></div><div className="cash-flow-metrics"><OperationsMetric label="SALDO AL INICIO" value={money(report.cash_flow.opening_balance)} icon="$"/><OperationsMetric label="APERTURAS EN EL PERIODO" value={money(report.cash_flow.opening_entries)} icon="＋"/><OperationsMetric label="ENTRADAS REGISTRADAS" value={money(report.cash_flow.inflows)} icon="↗"/><OperationsMetric label="SALIDAS REGISTRADAS" value={money(report.cash_flow.outflows)} icon="↘"/><OperationsMetric label="SALDO AL CIERRE" value={money(report.cash_flow.closing_balance)} icon="＝"/></div><p className="operations-report-basis">{report.cash_flow.basis}</p><div className="data-table-wrap"><table className="data-table"><thead><tr><th>CUENTA</th><th>TIPO</th><th>SALDO INICIAL</th><th>APERTURA EN PERIODO</th><th>ENTRADAS</th><th>SALIDAS</th><th>SALDO AL CIERRE</th></tr></thead><tbody>{report.cash_flow.accounts.map(account=><tr key={account.id}><td><b>{account.name}</b></td><td>{account.account_type==='cash'?'Efectivo':'Banco'}</td><td>{money(account.opening_balance)}</td><td>{money(account.opening_entries)}</td><td>{money(account.inflows)}</td><td>{money(account.outflows)}</td><td><b>{money(account.closing_balance)}</b></td></tr>)}</tbody></table>{!report.cash_flow.accounts.length&&<p className="muted-copy">No hay cuentas activas configuradas.</p>}</div></section>}
      <section className="dashboard-grid operations-report-grid">
        <article className="surface-card"><div className="section-title"><div><span className="eyebrow">EXISTENCIA ACTUAL</span><h2>Artículos por disponibilidad</h2></div>{report.stock.estimated_value!==null&&<strong>{money(report.stock.estimated_value)}</strong>}</div>{report.stock.items.length?<div className="stock-pie-layout"><div className="stock-pie" role="img" aria-label={`${stockStatusCounts.available} artículos disponibles, ${stockStatusCounts.low} con stock bajo y ${stockStatusCounts.depleted} agotados`} style={{background:`conic-gradient(${stockChartStops})`}}><div><b>{report.stock.item_count}</b><span>artículos</span></div></div><div className="stock-pie-legend">{stockStatusRows.map(row=><div key={row.label}><i style={{background:row.color}}/><span>{row.label}</span><b>{row.count}</b></div>)}</div></div>:<p className="muted-copy">No hay artículos registrados.</p>}</article>
        <article className="surface-card"><div className="section-title"><div><span className="eyebrow">GASTOS POR CATEGORÍA</span><h2>{report.expenses.count} registros</h2></div><strong>{money(report.expenses.total)}</strong></div>{report.expenses.by_category.length?<div className="operations-bars">{report.expenses.by_category.map(row=><div className="operations-bar-row" key={row.category}><span><b>{row.category}</b><small>{money(row.amount)}</small></span><div><i className="expense" style={{width:`${Math.min(100,Number(row.amount)/maxExpense*100)}%`}}/></div></div>)}</div>:<p className="muted-copy">No hay gastos en este periodo.</p>}</article>
      </section>
      <section className="dashboard-grid operations-report-grid operations-status-grid"><article className="surface-card"><div className="section-title"><div><span className="eyebrow">CLIENTES</span><h2>Por estado</h2></div></div>{statusRows(report.customers_by_status)}</article><article className="surface-card"><div className="section-title"><div><span className="eyebrow">ÓRDENES / PROYECTOS</span><h2>Por estado</h2></div></div>{statusRows(report.installations_by_status)}</article><article className="surface-card"><div className="section-title"><div><span className="eyebrow">PROVEEDORES</span><h2>Estado actual · {report.suppliers.total} en total</h2></div></div>{statusRows([{status:'Activos',count:report.suppliers.active},{status:'Inactivos',count:report.suppliers.inactive}])}</article></section>
      <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">STOCK DISPONIBLE</span><h2>Existencias detalladas por artículo</h2></div><span className="status-legend">{report.stock.item_count} artículos · cantidades actuales</span></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>ARTÍCULO</th><th>CATEGORÍA</th><th>EXISTENCIA FÍSICA</th><th>RESERVADO</th><th>DISPONIBLE</th><th>MÍNIMO</th><th>ESTADO</th></tr></thead><tbody>{report.stock.items.map(item=>{const available=Number(item.available_quantity);const low=available>0&&Number(item.minimum_quantity)>0&&available<=Number(item.minimum_quantity);const depleted=available<=0;return <tr key={item.id}><td><b>{item.name}</b></td><td>{item.category||'Sin categoría'}</td><td>{item.quantity} {item.unit}</td><td>{item.reserved_quantity} {item.unit}</td><td><b>{item.available_quantity} {item.unit}</b></td><td>{item.minimum_quantity} {item.unit}</td><td><span className={`stock-state ${depleted?'depleted':low?'low':'available'}`}>{depleted?'Agotado':low?'Stock bajo':'Disponible'}</span></td></tr>})}</tbody></table>{!report.stock.items.length&&<p className="muted-copy">No hay artículos registrados.</p>}</div></section>
      <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">KARDEX DEL PERIODO</span><h2>Entradas, salidas y actividad</h2>{report.movements.truncated&&<small className="status-legend">Se muestran los 500 movimientos más recientes; reduce el periodo para consultar menos.</small>}</div><button className="button button-outline" disabled={!report.movements.items.length} onClick={exportMovements}>Descargar CSV</button></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>ARTÍCULO</th><th>MOVIMIENTO</th><th>CANTIDAD</th><th>ORDEN / REFERENCIA</th>{report.movements.items.some(row=>row.unit_cost!==undefined)&&<th>COSTO UNITARIO</th>}</tr></thead><tbody>{report.movements.items.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-MX')}</td><td>{row.item_name}<small className="sub-cell">{row.created_by}</small></td><td>{movementNames[row.movement_type]||row.movement_type}</td><td>{row.quantity} {row.unit}</td><td>{row.installation_folio||'—'}<small className="sub-cell">{row.reason||'—'}</small></td>{report.movements.items.some(item=>item.unit_cost!==undefined)&&<td>{row.unit_cost==null?'Sin dato':money(row.unit_cost)}</td>}</tr>)}</tbody></table>{!report.movements.items.length&&<p className="muted-copy">No hay movimientos en el periodo.</p>}</div></section>
    </>}
  </div>;
}

function OperationsMetric({label,value,icon}:{label:string;value:string;icon:string}){return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className="metric-icon tone-sage">{icon}</i></div><strong>{value}</strong></article>;}
