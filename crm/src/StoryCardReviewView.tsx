import { useEffect, useMemo, useState } from 'react';
import './story-card-review.css';

type StoryCard = {
  id: string;
  story_id: string;
  version: number;
  iteration: string;
  stakeholder: string;
  source_literal: string;
  source_type: string;
  source_reference: string;
  source_attribution?: string | null;
  source_confidence?: string | null;
  source_occurred_at?: string | null;
  normalized_story: string;
  acceptance_criteria: string[];
  unresolved_questions: string[];
  linked_cards: string[];
  created_at: string;
};
type ChecklistItem = { criterion: string; checked: boolean };
type StoryReview = {
  id: string;
  story_id: string;
  history_card_id: string;
  story_version: number;
  review_version: number;
  checklist: ChecklistItem[];
  observations: string;
  reviewed_by: string;
  created_at: string;
};

const apiBase = '/api/v1';
async function api<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'No se pudo guardar la revisión.');
  }
  return response.json() as Promise<T>;
}
const displayDate = (value: string) => new Date(value).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });

export function StoryCardReviewView({ token }: { token: string }) {
  const [cards, setCards] = useState<StoryCard[]>([]);
  const [reviews, setReviews] = useState<StoryReview[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'todas' | 'pendientes' | 'progreso' | 'verificadas'>('todas');
  const [checked, setChecked] = useState<boolean[]>([]);
  const [observations, setObservations] = useState('');
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [cardRows, reviewRows] = await Promise.all([
        api<StoryCard[]>('/history-cards', token),
        api<StoryReview[]>('/history-card-reviews', token),
      ]);
      setCards(cardRows);
      setReviews(reviewRows);
      if (!selectedId && cardRows.length) setSelectedId(cardRows[0].story_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudieron cargar las storycards.');
    } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, [token]);

  const latestCards = useMemo(() => {
    const latest = new Map<string, StoryCard>();
    for (const card of cards) {
      const current = latest.get(card.story_id);
      if (!current || card.version > current.version) latest.set(card.story_id, card);
    }
    return [...latest.values()].sort((a, b) => Number(a.story_id.replace(/\D/g, '')) - Number(b.story_id.replace(/\D/g, '')));
  }, [cards]);
  const latestReviews = useMemo(() => {
    const latest = new Map<string, StoryReview>();
    for (const review of reviews) {
      const current = latest.get(review.story_id);
      if (!current || review.review_version > current.review_version) latest.set(review.story_id, review);
    }
    return latest;
  }, [reviews]);
  const selected = latestCards.find(card => card.story_id === selectedId) || latestCards[0] || null;
  const selectedReview = selected ? latestReviews.get(selected.story_id) : undefined;
  const selectedHistory = selected ? reviews.filter(review => review.story_id === selected.story_id).sort((a, b) => b.review_version - a.review_version) : [];

  function reviewStatus(card: StoryCard) {
    const review = latestReviews.get(card.story_id);
    if (!review || review.story_version !== card.version) return 'pendiente';
    const completed = review.checklist.filter(item => item.checked).length;
    if (review.checklist.length > 0 && completed === review.checklist.length) return 'verificada';
    return 'progreso';
  }
  const counts = useMemo(() => {
    const values = latestCards.map(reviewStatus);
    return { total: values.length, pendiente: values.filter(v => v === 'pendiente').length, progreso: values.filter(v => v === 'progreso').length, verificadas: values.filter(v => v === 'verificada').length };
  }, [latestCards, latestReviews]);
  const visibleCards = latestCards.filter(card => {
    const term = search.trim().toLocaleLowerCase('es-MX');
    const matchesSearch = !term || [card.story_id, card.normalized_story, card.stakeholder, card.iteration, card.source_literal].join(' ').toLocaleLowerCase('es-MX').includes(term);
    const status = reviewStatus(card);
    return matchesSearch && (filter === 'todas' || (filter === 'pendientes' && status === 'pendiente') || (filter === 'progreso' && status === 'progreso') || (filter === 'verificadas' && status === 'verificada'));
  });

  useEffect(() => {
    if (!selected) { setChecked([]); setObservations(''); setDirty(false); return; }
    const sameVersion = selectedReview?.story_version === selected.version;
    const saved = new Map((sameVersion ? selectedReview?.checklist : [])?.map(item => [item.criterion, item.checked]) || []);
    setChecked(selected.acceptance_criteria.map(criterion => saved.get(criterion) || false));
    setObservations(sameVersion ? selectedReview?.observations || '' : '');
    setDirty(false);
  }, [selected?.id, selected?.version, selectedReview?.id]);

  function chooseCard(storyId: string) {
    if (dirty && !window.confirm('Tienes cambios sin guardar. ¿Descartarlos y abrir otra tarjeta?')) return;
    setDirty(false);
    setSelectedId(storyId);
  }
  function toggleCriterion(index: number) {
    setChecked(values => values.map((value, itemIndex) => itemIndex === index ? !value : value));
    setDirty(true);
    setNotice('');
  }
  async function saveReview() {
    if (!selected) return;
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const created = await api<StoryReview>(`/history-cards/${encodeURIComponent(selected.story_id)}/reviews`, token, {
        method: 'POST',
        body: JSON.stringify({
          story_version: selected.version,
          checklist: selected.acceptance_criteria.map((criterion, index) => ({ criterion, checked: checked[index] || false })),
          observations,
        }),
      });
      setReviews(rows => [...rows, created]);
      setDirty(false);
      setNotice(`Revisión ${created.review_version} guardada para ${selected.story_id}.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo guardar la revisión.');
    } finally { setSaving(false); }
  }
  const completedCriteria = checked.filter(Boolean).length;
  const canSave = Boolean(selected && dirty && (completedCriteria > 0 || observations.trim()) && !saving);

  return <div className="story-review-page">
    <section className="story-review-heading">
      <div><span className="eyebrow">DISCOVERY · VALIDACIÓN COLABORATIVA</span><h2>Revisión de user story cards</h2><p>Revisa la historia con cada stakeholder, confirma criterios y deja las observaciones registradas por iteración.</p></div>
      <button className="button button-outline" onClick={() => void load()} disabled={loading || saving}>{loading ? 'Actualizando…' : 'Actualizar tarjetas'}</button>
    </section>
    <section className="story-review-summary" aria-label="Resumen de revisión">
      <article><small>TARJETAS</small><strong>{counts.total}</strong><span>Versiones vigentes</span></article>
      <article><small>PENDIENTES</small><strong>{counts.pendiente}</strong><span>Sin revisión de esta versión</span></article>
      <article><small>EN PROGRESO</small><strong>{counts.progreso}</strong><span>Checklist parcial</span></article>
      <article><small>VERIFICADAS</small><strong>{counts.verificadas}</strong><span>Criterios marcados</span></article>
    </section>
    {error && <p role="alert" className="error-message story-review-alert">{error}</p>}
    {notice && <p role="status" className="story-review-notice">✓ {notice}</p>}
    <div className="story-review-layout">
      <section className="surface-card story-review-table-card">
        <div className="story-review-controls"><label className="field"><span>Buscar tarjeta</span><input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="ID, stakeholder, frase…"/></label><label className="field"><span>Estado</span><select value={filter} onChange={event => setFilter(event.target.value as typeof filter)}><option value="todas">Todas ({counts.total})</option><option value="pendientes">Pendientes ({counts.pendiente})</option><option value="progreso">En progreso ({counts.progreso})</option><option value="verificadas">Verificadas ({counts.verificadas})</option></select></label></div>
        <div className="story-review-table-wrap"><table className="story-review-table"><thead><tr><th>Tarjeta</th><th>Stakeholder</th><th>Iteración / versión</th><th>Checklist</th><th>Estado</th></tr></thead><tbody>
          {visibleCards.map(card => {
            const status = reviewStatus(card);
            const review = latestReviews.get(card.story_id);
            const sameVersion = review?.story_version === card.version;
            const done = sameVersion ? review!.checklist.filter(item => item.checked).length : 0;
            return <tr key={card.story_id} className={selected?.story_id === card.story_id ? 'selected' : ''} onClick={() => chooseCard(card.story_id)} tabIndex={0} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); chooseCard(card.story_id); } }}>
              <td><b>{card.story_id}</b><small>{card.normalized_story}</small></td><td>{card.stakeholder}</td><td>{card.iteration}<small>v{card.version}</small></td><td>{sameVersion ? `${done}/${review!.checklist.length}` : `0/${card.acceptance_criteria.length}`}</td><td><span className={`story-review-status ${status}`}>{status === 'verificada' ? 'Verificada' : status === 'progreso' ? 'En progreso' : 'Pendiente'}</span></td>
            </tr>;
          })}
          {!loading && !visibleCards.length && <tr><td colSpan={5} className="story-review-empty">No hay tarjetas para este filtro.</td></tr>}
        </tbody></table></div>
        <small className="story-review-table-foot">Selecciona una fila para ver el relato, criterios, observaciones e historial de validaciones.</small>
      </section>
      <section className="surface-card story-review-detail" aria-label="Detalle de revisión">
        {!selected ? <div className="story-review-empty-detail">{loading ? 'Cargando storycards…' : 'No hay tarjetas registradas.'}</div> : <>
          <div className="story-review-detail-head"><div><span className="eyebrow">{selected.story_id} · VERSIÓN {selected.version}</span><h3>{selected.stakeholder}</h3><p>{selected.iteration}</p></div><span className={`story-review-status ${reviewStatus(selected)}`}>{reviewStatus(selected) === 'verificada' ? 'Verificada' : reviewStatus(selected) === 'progreso' ? 'En progreso' : 'Pendiente'}</span></div>
          <div className="story-review-story"><small>HISTORIA</small><p>{selected.normalized_story}</p><details><summary>Ver relato original y procedencia</summary><blockquote>{selected.source_literal}</blockquote><small>{selected.source_attribution || selected.stakeholder} · {selected.source_type} · {selected.source_reference}</small>{selected.source_confidence && <small>Fidelidad: {selected.source_confidence}</small>}{selected.source_occurred_at && <small>Fecha de origen: {selected.source_occurred_at}</small>}</details></div>
          <div className="story-review-section"><div><span className="eyebrow">CHECKLIST DE ACEPTACIÓN</span><b>{completedCriteria} de {selected.acceptance_criteria.length} confirmados</b></div>{selected.acceptance_criteria.length ? <ul className="story-review-checklist">{selected.acceptance_criteria.map((criterion, index) => <li key={`${index}-${criterion}`}><label><input type="checkbox" checked={checked[index] || false} onChange={() => toggleCriterion(index)}/><span>{criterion}</span></label></li>)}</ul> : <p className="story-review-muted">Esta tarjeta aún no tiene criterios registrados.</p>}</div>
          {selected.unresolved_questions.length > 0 && <div className="story-review-section"><span className="eyebrow">PREGUNTAS ABIERTAS / DEPENDENCIAS</span><ul className="story-review-open">{selected.unresolved_questions.map((question, index) => <li key={`${index}-${question}`}>{question}</li>)}</ul></div>}
          {selected.linked_cards.length > 0 && <p className="story-review-linked">Relacionada con: {selected.linked_cards.join(' · ')}</p>}
          <label className="field story-review-observations"><span>Observaciones de la revisión</span><textarea value={observations} maxLength={5000} onChange={event => { setObservations(event.target.value); setDirty(true); setNotice(''); }} placeholder="Acuerdos, dudas del stakeholder, contexto de la verificación…"/><small>{observations.length}/5000 · Cada guardado crea una versión de revisión y conserva las anteriores.</small></label>
          <div className="story-review-save"><span>{dirty ? 'Cambios sin guardar' : selectedReview ? `Última revisión por ${selectedReview.reviewed_by}` : 'Aún no se ha registrado una revisión'}</span><button className="button button-primary" onClick={() => void saveReview()} disabled={!canSave}>{saving ? 'Guardando…' : 'Guardar revisión'}</button></div>
          <div className="story-review-history"><span className="eyebrow">HISTORIAL DE REVISIONES · {selectedHistory.length}</span>{selectedHistory.length ? selectedHistory.map(review => <article key={review.id}><div><b>Revisión {review.review_version} · tarjeta v{review.story_version}</b><small>{review.reviewed_by} · {displayDate(review.created_at)}</small></div><p>{review.observations || 'Sin observaciones en esta revisión.'}</p><small>{review.checklist.filter(item => item.checked).length} de {review.checklist.length} criterios confirmados</small></article>) : <p className="story-review-muted">Las observaciones y checklist que guardes aparecerán aquí.</p>}</div>
        </>}
      </section>
    </div>
  </div>;
}
