import { useEffect, useState } from 'react';

export const COUNTRIES = ['United States', 'France', 'Germany', 'Romania'] as const;
export const CATEGORIES = ['Business', 'Health', 'Nation', 'Politics', 'Science', 'Technology', 'World'] as const;
export const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706'];

export type Kpi = {
  country: string; stories: number; days: number; first_date: string; last_date: string;
  outlets: number; lead_outlets: number; top10_share: number; single_share: number;
};
export type MonthConc = { country: string; month: string; stories: number; lead_outlets: number; top10_share: number; hhi: number };
export type CategoryRow = {
  country: string; category: string; stories: number; outlets: number; lead_outlets: number;
  top10_share: number; single_share: number; top_outlet: string; top_outlet_share: number;
};
export type OutletRow = {
  country: string; category?: string; outlet: string; website?: string;
  leads: number; appearances: number; lead_rate: number; fair_lead_rate: number | null; lead_share: number;
};
export type DayRow = { country: string; date: string; stories: number };

/** Load one dataset: public/data/<name>.json, written by pipeline/gnobs/export_json.py */
export function useData<T>(name: string): T | null {
  const [data, setData] = useState<T | null>(null);
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/${name}.json`)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => console.error(`failed to load ${name}`, e));
  }, [name]);
  return data;
}

export const pct = (v: number, digits = 0) => `${(v * 100).toFixed(digits)}%`;
export const int = (v: number) => v.toLocaleString('en-US');
