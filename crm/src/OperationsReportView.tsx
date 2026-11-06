import { useEffect, useState, type FormEvent } from 'react';

type OperationsReport = {
  basis: string;
  stock: { items:Array<{id:string;name:string;category:string;unit:string;quantity:number;reserved_quantity:number;available_quantity:number;minimum_quantity:number;low_stock:boolean;unit_cost?:number}>; item_count:number; low_stock_count:number; estimated_value:number|null };
  movements: { items:Array<{id:string;created_at:string;item_name:string;unit:string;movement_type:string;quantity:number;installation_folio:string|null;reason:string;created_by:string;unit_cost?:number|null}>; truncated:boolean; totals_by_type:Array<{movement_type:string;quantity:number}> };
  customers_by_status:Array<{status:string;count:number}>;
  suppliers:{total:number;active:number;inactive:number};
  installations_by_status:Array<{status:string;count:number}>;
  expenses:{total:number;by_category:Array<{category:string;amount:number}>;count:number};
};

const money = (amount:number) => new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:2}).format(amount);
const statusNames:Record<string,string> = {lead:'Prospecto',active:'Activo',qualified:'Calificado',assigned:'Asignada',scheduled:'Programada',in_progress:'En curso',closed:'Cerrada',cancelled:'Cancelada'};
const movementNames:Record<string,string> = {in:'Entrada',out:'Salida',return:'Devolución',waste:'Merma',consumption:'Consumo confirmado',consumption_return:'Consumo corregido'};

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

  const maxStock=Math.max(1,...(report?.stock.items.map(item=>Number(item.available_quantity))||[]));
  const maxExpense=Math.max(1,...(report?.expenses.by_category.map(item=>Number(item.amount))||[]));
  const statusRows=(rows:Array<{status:string;count:number}>)=>rows.length?<div className="operations-status-list">{rows.map(row=><div key={row.status}><span>{statusNames[row.status]||row.status}</span><b>{row.count}</b></div>)}</div>:<p className="muted-copy">Sin registros.</p>;
  return <div className="operations-report">
    <section className="surface-card operations-report-filter"><div><span className="eyebrow">REPORTES OPERATIVOS</span><h2>Existencias y actividad</h2></div><form onSubmit={applyFilters}><label>Desde<input type="date" value={fromDate} onChange={event=>setFromDate(event.target.value)} required/></label><label>Hasta<input type="date" value={toDate} onChange={event=>setToDate(event.target.value)} required/></label><button className="button button-primary" disabled={loading}>{loading?'Actualizando…':'Consultar'}</button></form></section>
    <p className="operations-report-basis">{report?.basis||'El reporte distingue existencias actuales de actividad registrada en el periodo seleccionado.'}</p>
    {error&&<p role="alert" className="error-message">{error}</p>}
    {report&&<>
      <section className="metric-grid"><OperationsMetric label="ARTÍCULOS" value={String(report.stock.item_count)} icon="▦"/><OperationsMetric label="STOCK BAJO" value={String(report.stock.low_stock_count)} icon="!"/><OperationsMetric label="MOVIMIENTOS" value={String(report.movements.items.length)} icon="↕"/><OperationsMetric label="GASTOS CAPTURADOS" value={money(report.expenses.total)} icon="$"/></section>
      <section className="dashboard-grid operations-report-grid">
        <article className="surface-card"><div className="section-title"><div><span className="eyebrow">EXISTENCIA ACTUAL</span><h2>Disponible por artículo</h2></div>{report.stock.estimated_value!==null&&<strong>{money(report.stock.estimated_value)}</strong>}</div>{report.stock.items.length?<div className="operations-bars">{report.stock.items.map(item=><div className="operations-bar-row" key={item.id}><span><b>{item.name}</b><small>{item.category||'Sin categoría'} · {item.available_quantity}/{item.quantity} {item.unit}</small></span><div><i className={item.low_stock?'low':''} style={{width:`${Math.min(100,Number(item.available_quantity)/maxStock*100)}%`}}/></div></div>)}</div>:<p className="muted-copy">No hay artículos registrados.</p>}</article>
        <article className="surface-card"><div className="section-title"><div><span className="eyebrow">GASTOS POR CATEGORÍA</span><h2>{report.expenses.count} registros</h2></div><strong>{money(report.expenses.total)}</strong></div>{report.expenses.by_category.length?<div className="operations-bars">{report.expenses.by_category.map(row=><div className="operations-bar-row" key={row.category}><span><b>{row.category}</b><small>{money(row.amount)}</small></span><div><i className="expense" style={{width:`${Math.min(100,Number(row.amount)/maxExpense*100)}%`}}/></div></div>)}</div>:<p className="muted-copy">No hay gastos en este periodo.</p>}</article>
      </section>
      <section className="dashboard-grid operations-report-grid operations-status-grid"><article className="surface-card"><div className="section-title"><div><span className="eyebrow">CLIENTES</span><h2>Por estado</h2></div></div>{statusRows(report.customers_by_status)}</article><article className="surface-card"><div className="section-title"><div><span className="eyebrow">ÓRDENES / PROYECTOS</span><h2>Por estado</h2></div></div>{statusRows(report.installations_by_status)}</article><article className="surface-card"><div className="section-title"><div><span className="eyebrow">PROVEEDORES</span><h2>Estado actual · {report.suppliers.total} en total</h2></div></div>{statusRows([{status:'Activos',count:report.suppliers.active},{status:'Inactivos',count:report.suppliers.inactive}])}</article></section>
      <section className="surface-card table-surface"><div className="table-toolbar"><div><span className="eyebrow">KARDEX DEL PERIODO</span><h2>Entradas, salidas y actividad</h2>{report.movements.truncated&&<small className="status-legend">Se muestran los 500 movimientos más recientes; reduce el periodo para consultar menos.</small>}</div><button className="button button-outline" disabled={!report.movements.items.length} onClick={exportMovements}>Descargar CSV</button></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>FECHA</th><th>ARTÍCULO</th><th>MOVIMIENTO</th><th>CANTIDAD</th><th>ORDEN / REFERENCIA</th>{report.movements.items.some(row=>row.unit_cost!==undefined)&&<th>COSTO UNITARIO</th>}</tr></thead><tbody>{report.movements.items.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-MX')}</td><td>{row.item_name}<small className="sub-cell">{row.created_by}</small></td><td>{movementNames[row.movement_type]||row.movement_type}</td><td>{row.quantity} {row.unit}</td><td>{row.installation_folio||'—'}<small className="sub-cell">{row.reason||'—'}</small></td>{report.movements.items.some(item=>item.unit_cost!==undefined)&&<td>{row.unit_cost==null?'Sin dato':money(row.unit_cost)}</td>}</tr>)}</tbody></table>{!report.movements.items.length&&<p className="muted-copy">No hay movimientos en el periodo.</p>}</div></section>
    </>}
  </div>;
}

function OperationsMetric({label,value,icon}:{label:string;value:string;icon:string}){return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className="metric-icon tone-sage">{icon}</i></div><strong>{value}</strong></article>;}
