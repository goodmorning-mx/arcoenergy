import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';

type IntakeMaterial = { id: string; item_id: string; item_name: string; requested_quantity: number; preissued_quantity: number; remaining_to_issue: number };
type IntakeInstallation = { id: string; folio?: string | null; status: string; customer?: { name: string; city: string }; materials?: IntakeMaterial[] };
type ReturnSource = { id: string; installation_id?: string | null; item_name: string; quantity: number; unit: string; movement_type: string; returnable_quantity?: number };
type Mode = 'issue' | 'return';

const acceptedFile = (file: File) => {
  const extension = file.name.toLowerCase().split('.').pop();
  return ['application/pdf', 'image/jpeg', 'image/png', 'image/webp'].includes(file.type)
    || ['pdf', 'jpg', 'jpeg', 'png', 'webp'].includes(extension || '');
};

export function InventoryIssueIntake({
  installations, movements, token, onSaved, announce,
}: {
  installations: IntakeInstallation[];
  movements: ReturnSource[];
  token: string;
  onSaved: () => Promise<void>;
  announce: (message: string, type?: 'success' | 'error' | 'info') => void;
}) {
  const [mode, setMode] = useState<Mode>('issue');
  const [installationId, setInstallationId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [movementId, setMovementId] = useState('');
  const [returnQuantity, setReturnQuantity] = useState('');
  const [condition, setCondition] = useState<'usable' | 'damaged'>('usable');
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const fileUrl = useMemo(() => file ? URL.createObjectURL(file) : '', [file]);
  const installation = installations.find(row => row.id === installationId);
  const issueMaterials = (installation?.materials || []).filter(row => row.remaining_to_issue > 0);
  const returnSources = movements.filter(row => row.installation_id === installationId && row.movement_type === 'out' && Number(row.returnable_quantity || 0) > 0);
  const isPdf = file?.type === 'application/pdf' || file?.name.toLowerCase().endsWith('.pdf');

  useEffect(() => () => { if (fileUrl) URL.revokeObjectURL(fileUrl); }, [fileUrl]);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] || null;
    setFailure('');
    if (!selected) { setFile(null); return; }
    if (!acceptedFile(selected)) { setFailure('Elige una imagen JPG, PNG, WebP o un archivo PDF.'); event.target.value = ''; return; }
    if (selected.size > 12 * 1024 * 1024) { setFailure('El archivo debe pesar 12 MB o menos.'); event.target.value = ''; return; }
    setFile(selected);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailure('');
    if (!file) { setFailure('Adjunta la solicitud para revisarla antes de registrar.'); return; }
    if (!installation) { setFailure('Selecciona una orden de trabajo.'); return; }
    let path = '';
    let payload: Record<string, unknown>;
    const reference = file.name.slice(0, 70);
    if (mode === 'issue') {
      const lines = issueMaterials.map(material => ({
        work_order_material_id: material.id,
        quantity: Number(quantities[material.id] || 0),
      })).filter(line => line.quantity > 0);
      if (!lines.length) { setFailure('Captura al menos una cantidad de la solicitud revisada.'); return; }
      path = '/api/v1/inventory/issue';
      payload = { installation_id: installation.id, document_reference: reference, lines };
    } else {
      const source = returnSources.find(row => row.id === movementId);
      if (!source) { setFailure('Selecciona la salida original del artículo que vas a devolver.'); return; }
      const quantity = Number(returnQuantity);
      if (!quantity || quantity <= 0 || quantity > Number(source.returnable_quantity)) { setFailure('La cantidad debe estar dentro de lo pendiente por devolver.'); return; }
      const note = String(new FormData(event.currentTarget).get('note') || '').trim();
      path = '/api/v1/inventory/returns';
      payload = {
        out_movement_id: source.id,
        quantity,
        condition,
        reason: `Solicitud ${reference}${note ? ` · ${note}` : ''}`.slice(0, 180),
      };
    }

    setBusy(true);
    try {
      const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'No se pudo registrar el movimiento.');
      await onSaved();
      setFile(null); setQuantities({}); setMovementId(''); setReturnQuantity('');
      const input = document.getElementById('work-order-scan') as HTMLInputElement | null;
      if (input) input.value = '';
      announce(mode === 'issue' ? 'Salida física registrada desde la solicitud revisada.' : condition === 'damaged' ? 'Merma ligada a la solicitud y a la orden registrada.' : 'Devolución ligada a la solicitud y a la orden registrada.');
    } catch (error) {
      setFailure(error instanceof Error ? error.message : 'No se pudo registrar el movimiento.');
    } finally { setBusy(false); }
  }

  return <section className="surface-card issue-intake">
    <div className="section-title"><div><span className="eyebrow">ORDEN DE SERVICIO</span><h2>Preparar salida o devolución</h2></div><span className="status-chip status-approved">Revisión requerida</span></div>
    <p className="muted-copy">Adjunta la foto/PDF, transcribe y revisa cantidades contra la solicitud, y confirma el movimiento. La lectura automática de escritura a mano no está habilitada.</p>
    <div className="issue-mode" role="group" aria-label="Tipo de movimiento"><button type="button" className={mode === 'issue' ? 'selected' : ''} onClick={() => { setMode('issue'); setFailure(''); }}>Salida de material</button><button type="button" className={mode === 'return' ? 'selected' : ''} onClick={() => { setMode('return'); setFailure(''); }}>Devolución / merma</button></div>
    <form className="issue-form" onSubmit={event => void submit(event)}>
      <label className="field"><span>Orden de trabajo</span><select value={installationId} onChange={event => { setInstallationId(event.target.value); setQuantities({}); setMovementId(''); setReturnQuantity(''); }} required><option value="">Selecciona una orden</option>{installations.filter(row => row.status !== 'closed').map(row => <option key={row.id} value={row.id}>{row.folio || 'Orden'} · {row.customer?.name || 'Cliente'} · {row.customer?.city || 'Ubicación pendiente'}</option>)}</select></label>
      <label className="field"><span>Solicitud de materiales · foto o PDF</span><input id="work-order-scan" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" capture="environment" onChange={chooseFile} required/><small className="muted-copy">Máximo 12 MB. El archivo se previsualiza en este dispositivo; por ahora no se conserva en Drive.</small></label>
      {fileUrl && <div className="issue-preview" aria-label="Vista previa de la solicitud">{isPdf ? <iframe src={fileUrl} title="Solicitud de materiales en PDF" /> : <img src={fileUrl} alt="Solicitud de materiales adjunta para revisión"/>}<span>{file?.name}</span></div>}
      {mode === 'issue' ? <div className="issue-lines"><h3>Material solicitado · captura revisada</h3>{issueMaterials.length ? issueMaterials.map(material => <label className="issue-line" key={material.id}><span><b>{material.item_name}</b><small>Solicitado: {material.requested_quantity} · Por entregar: {material.remaining_to_issue}</small></span><input aria-label={`Cantidad de salida para ${material.item_name}`} type="number" min="0" max={material.remaining_to_issue} step="0.01" placeholder="0" value={quantities[material.id] || ''} onChange={event => setQuantities(current => ({ ...current, [material.id]: event.target.value }))}/></label>) : <p className="muted-copy">Esta orden no tiene material pendiente por entregar.</p>}</div> : <div className="issue-lines"><h3>Artículo devuelto o dañado</h3><label className="field"><span>Salida original</span><select value={movementId} onChange={event => { setMovementId(event.target.value); setReturnQuantity(''); }} required><option value="">Selecciona material de esta orden</option>{returnSources.map(row => <option key={row.id} value={row.id}>{row.item_name} · quedan {row.returnable_quantity} {row.unit}</option>)}</select></label>{movementId && <><label className="field"><span>Cantidad</span><input type="number" min="0.01" max={returnSources.find(row => row.id === movementId)?.returnable_quantity} step="0.01" value={returnQuantity} onChange={event => setReturnQuantity(event.target.value)} required/></label><label className="field"><span>Condición</span><select value={condition} onChange={event => setCondition(event.target.value as 'usable' | 'damaged')}><option value="usable">Reutilizable · vuelve al almacén</option><option value="damaged">Dañado · registrar merma</option></select></label><label className="field"><span>Nota (opcional)</span><input name="note" maxLength={80} placeholder="Condición o comentario"/></label></>}</div>}
      {failure && <p className="error-message" role="alert">{failure}</p>}
      <div className="issue-confirm"><p>El stock se actualiza al confirmar. La solicitud original no se procesa automáticamente y el archivo no se almacena todavía.</p><button className="button button-primary" disabled={busy || !file || !installation || (mode === 'issue' ? !issueMaterials.length : !movementId)}>{busy ? 'Registrando…' : mode === 'issue' ? 'Confirmar salida física' : 'Confirmar devolución'}</button></div>
    </form>
  </section>;
}
