import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { createAuthClient } from '@goodmorning/gm-auth';

type Identity = { user_id: string; organization_id: string; roles: string[]; permissions: string[]; email?: string | null; name?: string | null };
type Tokens = { access_token: string; refresh_token: string; expires_in: number; identity: Identity };
type AuthValue = { identity: Identity | null; accessToken: string | null; loading: boolean; error: string | null; login(email: string, password: string, remember?: boolean): Promise<void>; logout(): Promise<void> };
const KEY = 'arcoenergy-auth-tokens';
const client = createAuthClient(import.meta.env.VITE_API_URL || '/api');
const Context = createContext<AuthValue | null>(null);

export function PersistentAuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<Tokens | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const tokensRef = useRef<Tokens | null>(null);
  const renewing = useRef(false);
  const update = (next: Tokens | null) => { tokensRef.current = next; setTokens(next); if (next) localStorage.setItem(KEY, JSON.stringify(next)); else localStorage.removeItem(KEY); };
  const renew = async () => {
    const current = tokensRef.current;
    if (!current || renewing.current) return;
    renewing.current = true;
    const rotate = async () => {
      const latest = localStorage.getItem(KEY);
      if (latest) {
        try {
          const parsed = JSON.parse(latest) as Tokens;
          if (parsed.refresh_token !== current.refresh_token) { update(parsed); return; }
        } catch { /* A malformed value is replaced by a fresh token or cleared below. */ }
      }
      update(await client.refresh(current.refresh_token));
    };
    try {
      if (navigator.locks) await navigator.locks.request(`${KEY}-refresh`, rotate);
      else await rotate();
      setError(null);
    }
    catch { update(null); setError('La sesión terminó. Inicia sesión nuevamente.'); }
    finally { renewing.current = false; }
  };
  useEffect(() => {
    let mounted = true;
    try { const saved = localStorage.getItem(KEY) || localStorage.getItem('gm-auth-tokens') || sessionStorage.getItem('gm-auth-tokens'); if (saved) tokensRef.current = JSON.parse(saved) as Tokens; }
    catch { localStorage.removeItem(KEY); localStorage.removeItem('gm-auth-tokens'); sessionStorage.removeItem('gm-auth-tokens'); }
    void (async () => { if (tokensRef.current) await renew(); if (mounted) setLoading(false); })();
    return () => { mounted = false; };
  }, []);
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key !== KEY) return;
      if (!event.newValue) { tokensRef.current = null; setTokens(null); return; }
      try { const next = JSON.parse(event.newValue) as Tokens; tokensRef.current = next; setTokens(next); }
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
