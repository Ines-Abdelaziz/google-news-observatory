import { useEffect, useState } from 'react';

export const COUNTRIES = ['United States', 'France', 'Germany', 'Romania'] as const;
export const CATEGORIES = ['Business', 'Health', 'Nation', 'Politics', 'Science', 'Technology', 'World'] as const;
export const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706'];
export const PALETTE = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#0891b2', '#db2777', '#65a30d', '#ea580c', '#475569'];
export const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Row = Record<string, any>;

export type Loaded<T> = { data: T | null; missing: boolean };

/** Load one dataset: public/data/<name>.json, written by the pipeline. */
export function useData<T = Row[]>(name: string): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ data: null, missing: false });
  useEffect(() => {
    let alive = true;
    fetch(`${import.meta.env.BASE_URL}data/${name}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d) => alive && setState({ data: d, missing: false }))
      .catch(() => alive && setState({ data: null, missing: true }));
    return () => { alive = false; };
  }, [name]);
  return state;
}

export const pct = (v: number | null | undefined, digits = 0) =>
  v == null || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(digits)}%`;
export const int = (v: number | null | undefined) => (v == null ? '—' : Math.round(v).toLocaleString('en-US'));
export const monthLabel = (m: string) =>
  new Date(m.length === 7 ? `${m}-01T00:00:00Z` : `${m}T00:00:00Z`).toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
export const dayLabel = (d: string) =>
  new Date(`${d}T00:00:00Z`).toLocaleString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });

/** Pivot long rows into one object per x value with one key per series. */
export function pivot(rows: Row[], x: string, series: string, value: string | ((r: Row) => number)) {
  const get = typeof value === 'string' ? (r: Row) => r[value] : value;
  const byX = new Map<string, Row>();
  for (const r of rows) {
    const k = String(r[x]);
    if (!byX.has(k)) byX.set(k, { x: k });
    byX.get(k)![r[series]] = (byX.get(k)![r[series]] ?? 0) + get(r);
  }
  return [...byX.values()].sort((a, b) => String(a.x).localeCompare(String(b.x)));
}

/** Turn values into shares of their row total (for 100% stacked charts). */
export function toShares(rows: Row[], keys: string[]) {
  return rows.map((r) => {
    const total = keys.reduce((s, k) => s + (r[k] ?? 0), 0) || 1;
    const o: Row = { x: r.x };
    for (const k of keys) o[k] = (r[k] ?? 0) / total;
    return o;
  });
}
