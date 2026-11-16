import { ReactNode } from 'react';
import { CATEGORIES, COUNTRIES, Loaded } from '../data';

export function Card({ id, title, sub, children }: { id?: string; title: string; sub?: ReactNode; children: ReactNode }) {
  return (
    <section className="card" id={id}>
      <h2>{title}</h2>
      {sub && <p className="sub">{sub}</p>}
      {children}
    </section>
  );
}

/** Render children once a dataset is loaded; explain when it has not been computed. */
export function WithData<T>({ d, children }: { d: Loaded<T>; children: (data: T) => ReactNode }) {
  if (d.missing) return <p className="note">Not computed yet: run the matching pipeline step (see docs/MAINTAINING.md).</p>;
  if (!d.data) return <p className="note">Loading…</p>;
  if (Array.isArray(d.data) && d.data.length === 0) return <p className="note">No data for this view.</p>;
  return <>{children(d.data)}</>;
}

export function Picker<T extends string>({ label, value, options, onChange }: {
  label: string; value: T; options: readonly T[]; onChange: (v: T) => void;
}) {
  return (
    <label className="picker">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value as T)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

export const EditionPicker = ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
  <Picker label="Edition" value={value} options={COUNTRIES as unknown as string[]} onChange={onChange} />
);

export const CategoryPicker = ({ value, onChange, withAll = false }: {
  value: string; onChange: (v: string) => void; withAll?: boolean;
}) => (
  <Picker label="Section" value={value}
    options={(withAll ? ['All', ...CATEGORIES] : [...CATEGORIES]) as string[]} onChange={onChange} />
);

export function Table({ columns, rows, keyOf }: {
  columns: { label: string; render: (r: Record<string, unknown>) => ReactNode; left?: boolean; wrap?: boolean }[];
  rows: Record<string, unknown>[];
  keyOf: (r: Record<string, unknown>, i: number) => string;
}) {
  return (
    <div className="wrap">
      <table>
        <thead><tr>{columns.map((c) => <th key={c.label} className={c.left ? 'left' : ''}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={keyOf(r, i)}>
              {columns.map((c) => <td key={c.label} className={`${c.left ? 'left' : ''} ${c.wrap ? 'wrapcell' : ''}`}>{c.render(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
