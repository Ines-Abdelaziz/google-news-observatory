import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { COLORS, COUNTRIES, DayRow, MonthConc, int, pct } from '../data';

/** Pivot long rows (country, x, value) into one object per x with a key per country. */
function pivot<T>(rows: T[], x: (r: T) => string, country: (r: T) => string, value: (r: T) => number) {
  const byX = new Map<string, Record<string, string | number>>();
  for (const r of rows) {
    const k = x(r);
    if (!byX.has(k)) byX.set(k, { x: k });
    byX.get(k)![country(r)] = value(r);
  }
  return [...byX.values()].sort((a, b) => String(a.x).localeCompare(String(b.x)));
}

export function ConcentrationChart({ rows }: { rows: MonthConc[] }) {
  const data = pivot(rows, (r) => r.month, (r) => r.country, (r) => r.top10_share);
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#e5e7eb" vertical={false} />
        <XAxis dataKey="x" tickFormatter={(m: string) => new Date(m + '-01T00:00:00Z').toLocaleString('en-US', { month: 'short', timeZone: 'UTC' })} />
        <YAxis domain={[0, 1]} tickFormatter={(v: number) => pct(v)} width={44} />
        <Tooltip formatter={(v: number) => pct(v, 1)} />
        <Legend />
        {COUNTRIES.map((c, i) => (
          <Line key={c} dataKey={c} stroke={COLORS[i]} strokeWidth={2} dot={{ r: 3 }} type="linear" connectNulls={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CoverageChart({ rows }: { rows: DayRow[] }) {
  const data = pivot(rows.filter((r) => r.stories > 0), (r) => r.date, (r) => r.country, (r) => r.stories);
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#e5e7eb" vertical={false} />
        <XAxis dataKey="x" minTickGap={40} />
        <YAxis tickFormatter={int} width={50} />
        <Tooltip formatter={(v: number) => int(v)} />
        <Legend />
        {COUNTRIES.map((c, i) => (
          <Line key={c} dataKey={c} stroke={COLORS[i]} strokeWidth={1.5} dot={false} type="linear" connectNulls={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
