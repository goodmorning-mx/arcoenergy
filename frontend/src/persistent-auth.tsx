import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { createAuthClient } from '@goodmorning/gm-auth';

type Identity = { user_id: string; organization_id: string; roles: string[]; permissions: string[]; email?: string | null; name?: string | null };
type Tokens = { access_token: string; refresh_token: string; expires_in: number; expires_at?: number; identity: Identity };
type AuthValue = { identity: Identity | null; accessToken: string | null; loading: boolean; error: string | null; login(email: string, password: string, remember?: boolean): Promise<void>; logout(): Promise<void> };
const KEY = 'arcoenergy-auth-tokens';
const client = createAuthClient(import.meta.env.VITE_API_URL || '/api');
const Context = createContext<AuthValue | null>(null);
class InvalidSessionError extends Error {}
async function refreshTokens(token: string): Promise<Tokens> {
  const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/auth/refresh`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: token }) });
  if (response.status === 401) throw new InvalidSessionError('Invalid refresh token.');
  if (!response.ok) throw new Error('Session refresh temporarily unavailable.');
  return response.json() as Promise<Tokens>;
}

export function PersistentAuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<Tokens | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const tokensRef = useRef<Tokens | null>(null);
  const renewing = useRef(false);
  const update = (next: Tokens | null) => {
    const normalized = next ? { ...next, expires_at: next.expires_at || Date.now() + next.expires_in * 1000 } : null;
    tokensRef.current = normalized; setTokens(normalized);
    if (normalized) localStorage.setItem(KEY, JSON.stringify(normalized)); else localStorage.removeItem(KEY);
    localStorage.removeItem('gm-auth-tokens'); sessionStorage.removeItem('gm-auth-tokens');
  };
  const renew = async (force = false) => {
    const current = tokensRef.current;
    if (!current || renewing.current) return;
    if (!force && current.expires_at && current.expires_at - Date.now() > 90_000) return;
    renewing.current = true;
    const rotate = async () => {
      const latest = localStorage.getItem(KEY);
      if (latest) {
        try {
          const parsed = JSON.parse(latest) as Tokens;
          if (parsed.refresh_token !== current.refresh_token) { update(parsed); return; }
        } catch { /* A malformed value is replaced by a fresh token or cleared below. */ }
      }
      update(await refreshTokens(current.refresh_token));
    };
    try {
      if (navigator.locks) await navigator.locks.request(`${KEY}-refresh`, rotate);
      else await rotate();
      setError(null);
    }
    catch (cause) {
      if (cause instanceof InvalidSessionError) { update(null); setError('La sesión ya no está activa. Inicia sesión nuevamente.'); }
      else { setError(null); window.setTimeout(() => void renew(), 30_000); }
    }
    finally { renewing.current = false; }
  };
  useEffect(() => {
    let mounted = true;
    try { const saved = localStorage.getItem(KEY) || localStorage.getItem('gm-auth-tokens') || sessionStorage.getItem('gm-auth-tokens'); if (saved) tokensRef.current = JSON.parse(saved) as Tokens; }
    catch { localStorage.removeItem(KEY); localStorage.removeItem('gm-auth-tokens'); sessionStorage.removeItem('gm-auth-tokens'); }
    void (async () => { if (tokensRef.current) await renew(true); if (mounted) setLoading(false); })();
    return () => { mounted = false; };
  }, []);
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key !== KEY) return;
      if (!event.newValue) { tokensRef.current = null; setTokens(null); return; }
      try { const next = JSON.parse(event.newValue) as Tokens; tokensRef.current = next.expires_at ? next : { ...next, expires_at: Date.now() + next.expires_in * 1000 }; setTokens(tokensRef.current); }
      catch { tokensRef.current = null; setTokens(null); }
    };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);
  useEffect(() => {
    if (!tokens) return;
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') void renew(); }, Math.max(60_000, (tokens.expires_in - 90) * 1000));
    const onFocus = () => { if (document.visibilityState === 'visible') void renew(); };
    document.addEventListener('visibilitychange', onFocus);
    return () => { window.clearInterval(timer); document.removeEventListener('visibilitychange', onFocus); };
  }, [tokens]);
  const value = useMemo<AuthValue>(() => ({
    identity: tokens?.identity ?? null, accessToken: tokens?.access_token ?? null, loading, error,
    async login(email, password) { setLoading(true); setError(null); try { update(await client.login(email, password)); } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.'); throw e; } finally { setLoading(false); } },
    async logout() { const current = tokensRef.current; update(null); setError(null); if (current) await client.logout(current.refresh_token).catch(() => undefined); },
  }), [tokens, loading, error]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useAuth() { const value = useContext(Context); if (!value) throw new Error('PersistentAuthProvider is required.'); return value; }
