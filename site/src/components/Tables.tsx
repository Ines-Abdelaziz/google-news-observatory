import { CategoryRow, COUNTRIES, Kpi, OutletRow, int, pct } from '../data';

export function KpiTable({ rows }: { rows: Kpi[] }) {
  return (
    <div className="wrap">
      <table>
        <thead>
          <tr>
            <th>Edition</th><th>Stories</th><th>Days collected</th><th>Outlets seen</th>
            <th>Outlets that ever lead</th><th>Top-10 share</th><th>Single-article stories</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.country}>
              <td>{r.country}</td><td>{int(r.stories)}</td><td>{int(r.days)}</td><td>{int(r.outlets)}</td>
              <td>{int(r.lead_outlets)}</td><td>{pct(r.top10_share)}</td><td>{pct(r.single_share)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Rows: categories; columns: editions; cell shading by value. */
export function CategoryMatrix({ rows, value, format }: {
  rows: CategoryRow[]; value: (r: CategoryRow) => number; format: (v: number) => string;
}) {
  const topics = [...new Set(rows.map((r) => r.category))].sort();
  const max = Math.max(...rows.map(value));
  return (
    <div className="wrap">
      <table>
        <thead><tr><th>Category</th>{COUNTRIES.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {topics.map((t) => (
            <tr key={t}>
              <td>{t}</td>
              {COUNTRIES.map((c) => {
                const r = rows.find((x) => x.category === t && x.country === c);
                const v = r ? value(r) : 0;
                return (
                  <td key={c} style={{ background: `rgba(37, 99, 235, ${(0.55 * v) / max})` }}>
                    {r ? format(v) : '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CategoryOverview({ rows }: { rows: CategoryRow[] }) {
  return (
    <div className="wrap">
      <table>
        <thead>
          <tr>
            <th>Edition</th><th>Stories</th><th>Outlets seen</th><th>Outlets that ever lead</th>
            <th>Top-10 share</th><th>Single-article stories</th><th>Top outlet</th><th>Its share of leads</th>
          </tr>
        </thead>
        <tbody>
          {COUNTRIES.map((c) => rows.find((r) => r.country === c)).filter(Boolean).map((r) => (
            <tr key={r!.country}>
              <td>{r!.country}</td><td>{int(r!.stories)}</td><td>{int(r!.outlets)}</td><td>{int(r!.lead_outlets)}</td>
              <td>{pct(r!.top10_share)}</td><td>{pct(r!.single_share)}</td><td>{r!.top_outlet}</td>
              <td>{pct(r!.top_outlet_share, 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function OutletTables({ rows }: { rows: OutletRow[] }) {
  return (
    <div className="grid4">
      {COUNTRIES.map((c) => (
        <div key={c}>
          <h3>{c}</h3>
          <div className="wrap">
            <table>
              <thead><tr><th>Outlet</th><th>Leads</th><th>Lead rate</th><th>Fair rate</th><th>Share</th></tr></thead>
              <tbody>
                {rows.filter((r) => r.country === c).map((r) => (
                  <tr key={r.outlet}>
                    <td className="outlet">{r.outlet}</td><td>{int(r.leads)}</td>
                    <td>{pct(r.lead_rate)}</td>
                    <td>{r.fair_lead_rate == null ? '—' : pct(r.fair_lead_rate)}</td><td>{pct(r.lead_share, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
