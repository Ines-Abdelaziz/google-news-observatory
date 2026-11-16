import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, SimulationNodeDatum } from 'd3-force';
import { COLORS, COUNTRIES, PALETTE, Row, int, pct } from '../data';

const grid = <CartesianGrid stroke="#e5e7eb" vertical={false} />;

/** One line per series; data already pivoted ({x, seriesA, seriesB...}). */
export function Lines({ data, keys, yFormat = int, xFormat, height = 280, yDomain, dots = false }: {
  data: Row[]; keys: string[]; yFormat?: (v: number) => string; xFormat?: (x: string) => string;
  height?: number; yDomain?: [number, number]; dots?: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        {grid}
        <XAxis dataKey="x" tickFormatter={xFormat} minTickGap={30} />
        <YAxis tickFormatter={yFormat} width={56} domain={yDomain ?? [0, 'auto']} />
        <Tooltip formatter={(v: number) => yFormat(v)} labelFormatter={(l: string) => (xFormat ? xFormat(l) : l)} />
        <Legend />
        {keys.map((k) => (
          <Line key={k} dataKey={k} stroke={colorFor(k, keys)} strokeWidth={2} dot={dots ? { r: 3 } : false}
            type="linear" connectNulls={false} isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

/** Stacked areas; with shares=true each x sums to 100%. */
export function StackedArea({ data, keys, shares = false, xFormat, height = 300 }: {
  data: Row[]; keys: string[]; shares?: boolean; xFormat?: (x: string) => string; height?: number;
}) {
  const fmt = shares ? (v: number) => pct(v) : int;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }} stackOffset={shares ? 'expand' : 'none'}>
        {grid}
        <XAxis dataKey="x" tickFormatter={xFormat} minTickGap={30} />
        <YAxis tickFormatter={fmt} width={56} />
        <Tooltip formatter={(v: number) => (shares ? int(v) : int(v))} labelFormatter={(l: string) => (xFormat ? xFormat(l) : l)} />
        <Legend />
        {keys.map((k, i) => (
          <Area key={k} dataKey={k} stackId="1" type="linear" stroke={PALETTE[i % PALETTE.length]}
            fill={PALETTE[i % PALETTE.length]} fillOpacity={0.55} isAnimationActive={false} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Horizontal stacked bars, one bar per category of `data` (field x), values as shares. */
export function StackedBars({ data, keys, height, shares = true }: {
  data: Row[]; keys: string[]; height?: number; shares?: boolean;
}) {
  const fmt = shares ? (v: number) => pct(v) : int;
  return (
    <ResponsiveContainer width="100%" height={height ?? 60 + data.length * 44}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 16, bottom: 0, left: 10 }}>
        <CartesianGrid stroke="#e5e7eb" horizontal={false} />
        <XAxis type="number" tickFormatter={fmt} domain={shares ? [0, 1] : [0, 'auto']} />
        <YAxis type="category" dataKey="x" width={110} />
        <Tooltip formatter={(v: number) => fmt(v)} />
        <Legend />
        {keys.map((k, i) => (
          <Bar key={k} dataKey={k} stackId="1" fill={k === 'unknown' || k === 'other' ? '#cbd5e1' : PALETTE[i % PALETTE.length]}
            isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Simple horizontal bars: rows with a label and a value. */
export function HBars({ rows, label, value, format = int, color = COLORS[0], height }: {
  rows: Row[]; label: string; value: string; format?: (v: number) => string; color?: string; height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height ?? 30 + rows.length * 26}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 40, bottom: 0, left: 10 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey={label} width={170} interval={0} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => format(v)} />
        <Bar dataKey={value} fill={color} isAnimationActive={false}
          label={{ position: 'right', formatter: (v: number) => format(v), fontSize: 11 }} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Grouped vertical bars: data pivoted with x and one key per series. */
export function Bars({ data, keys, format = int, xFormat, height = 280 }: {
  data: Row[]; keys: string[]; format?: (v: number) => string; xFormat?: (x: string) => string; height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        {grid}
        <XAxis dataKey="x" tickFormatter={xFormat} />
        <YAxis tickFormatter={format} width={56} />
        <Tooltip formatter={(v: number) => format(v)} labelFormatter={(l: string) => (xFormat ? xFormat(l) : l)} />
        <Legend />
        {keys.map((k) => <Bar key={k} dataKey={k} fill={colorFor(k, keys)} isAnimationActive={false} />)}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Color a series: editions keep their color everywhere, others use the palette. */
export function colorFor(key: string, keys: string[]) {
  const e = (COUNTRIES as readonly string[]).indexOf(key);
  return e >= 0 ? COLORS[e] : PALETTE[keys.indexOf(key) % PALETTE.length];
}

/** Grid of colored cells. rows x cols, value(r, c) in [0, max]. */
export function Heatmap({ rows, cols, value, format, rowLabel, colLabel, max }: {
  rows: string[]; cols: string[]; value: (r: string, c: string) => number | null;
  format: (v: number) => string; rowLabel?: (r: string) => string; colLabel?: (c: string) => string; max?: number;
}) {
  const vals = rows.flatMap((r) => cols.map((c) => value(r, c) ?? 0));
  const top = max ?? Math.max(...vals, 1e-9);
  return (
    <div className="wrap">
      <table className="heat">
        <thead><tr><th />{cols.map((c) => <th key={c}>{colLabel ? colLabel(c) : c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <th className="left">{rowLabel ? rowLabel(r) : r}</th>
              {cols.map((c) => {
                const v = value(r, c);
                return (
                  <td key={c} title={v == null ? '' : format(v)}
                    style={{ background: v == null ? 'transparent' : `rgba(37, 99, 235, ${(0.85 * v) / top})`,
                      color: v != null && v / top > 0.6 ? 'white' : undefined }}>
                    {v == null ? '' : format(v)}
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

type Node = SimulationNodeDatum & { id: string; size: number; rate: number | null };

/** Force-directed network of outlets: node size = appearances, link width = strength. */
export function Network({ nodes, edges }: {
  nodes: { id: string; size: number; rate: number | null }[];
  edges: { source: string; target: string; strength: number }[];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);
  const height = 520;
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(320, e.contentRect.width)));
    if (ref.current) ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  const layout = useMemo(() => {
    const maxSize = Math.max(...nodes.map((n) => n.size), 1);
    const ns: Node[] = nodes.map((n) => ({ ...n }));
    const ls = edges.map((e) => ({ ...e }));
    const r = (n: Node) => 5 + 18 * Math.sqrt(n.size / maxSize);
    const sim = forceSimulation(ns)
      .force('link', forceLink<Node, typeof ls[number] & { source: string | Node; target: string | Node }>(ls as never)
        .id((d) => d.id).distance(120).strength((l) => 0.1 + l.strength))
      .force('charge', forceManyBody().strength(-500))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collide', forceCollide<Node>().radius((d) => r(d) + 2))
      .stop();
    for (let i = 0; i < 300; i++) sim.tick();
    // stretch the layout to fill the box
    const xs = ns.map((n) => n.x ?? 0), ys = ns.map((n) => n.y ?? 0);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    ns.forEach((n) => {
      n.x = 60 + ((n.x ?? 0) - x0) / (x1 - x0 || 1) * (width - 120);
      n.y = 40 + ((n.y ?? 0) - y0) / (y1 - y0 || 1) * (height - 70);
    });
    return { ns, ls: ls as unknown as { source: Node; target: Node; strength: number }[], r };
  }, [nodes, edges, width]);
  const [hover, setHover] = useState<string | null>(null);
  const near = new Set(hover ? layout.ls.filter((l) => l.source.id === hover || l.target.id === hover)
    .flatMap((l) => [l.source.id, l.target.id]) : []);
  return (
    <div ref={ref} className="network">
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Network of outlets appearing in the same story cards">
        {layout.ls.map((l, i) => (
          <line key={i} x1={l.source.x} y1={l.source.y} x2={l.target.x} y2={l.target.y}
            stroke={hover && (l.source.id === hover || l.target.id === hover) ? '#2563eb' : '#cbd5e1'}
            strokeWidth={0.5 + 4 * l.strength} />
        ))}
        {layout.ns.map((n) => (
          <g key={n.id} transform={`translate(${n.x},${n.y})`} onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)}
            opacity={hover && hover !== n.id && !near.has(n.id) ? 0.25 : 1}>
            <circle r={layout.r(n)} fill={COLORS[0]} fillOpacity={0.25 + 0.6 * (n.rate ?? 0)} stroke="#1e3a8a" strokeWidth={0.8}>
              <title>{`${n.id}: ${int(n.size)} appearances, fair lead rate ${pct(n.rate)}`}</title>
            </circle>
            <text y={-layout.r(n) - 3} textAnchor="middle" fontSize={11} fill="#111827">{n.id}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}
