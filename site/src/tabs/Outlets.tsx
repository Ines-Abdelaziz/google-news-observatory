import { useMemo, useState } from 'react';
import { Bars, HBars, Lines, Network, StackedBars } from '../components/Plots';
import { Card, CategoryPicker, EditionPicker, Table, WithData } from '../components/Ui';
import { COUNTRIES, Row, dayLabel, int, monthLabel, pct, pivot, toShares, useData } from '../data';

const TYPES = ['commercial', 'public service', 'wire agency', 'aggregator', 'state-controlled', 'other'];
const ORIGINS = ['domestic', 'foreign', 'unknown'];

function mixRows(rows: Row[], cat: string, key: string, keys: string[], measure: 'leads' | 'appearances') {
  const p = pivot(rows.filter((r) => r.category === cat), 'country', key, measure);
  const ordered = COUNTRIES.map((c) => p.find((r) => r.x === c)).filter(Boolean) as Row[];
  return toShares(ordered, keys);
}

export default function Outlets() {
  const div = useData('outlet_diversity_weekly');
  const churn = useData('outlet_churn_monthly');
  const types = useData('type_mix');
  const origin = useData('origin_mix');
  const state = useData('state_media');
  const nodes = useData('coappearance_nodes');
  const edges = useData('coappearance_edges');
  const cover = useData('label_coverage');
  const [cat, setCat] = useState('All');
  const [ed, setEd] = useState('United States');
  return (
    <>
      <Card title="How many outlets make it into the feeds?" sub="Distinct outlets appearing in story cards each week, and distinct outlets that lead at least one story.">
        <WithData d={div}>{(rows) => (
          <div className="grid2">
            <div><h3>Outlets appearing</h3>
              <Lines data={pivot(rows, 'week', 'country', 'outlets')} keys={[...COUNTRIES]} xFormat={dayLabel} height={240} /></div>
            <div><h3>Outlets leading</h3>
              <Lines data={pivot(rows, 'week', 'country', 'lead_outlets')} keys={[...COUNTRIES]} xFormat={dayLabel} height={240} /></div>
          </div>
        )}</WithData>
      </Card>
      <Card title="New outlets each month" sub="Outlets seen for the first time that month (first and last months left out).">
        <WithData d={churn}>{(rows) => (
          <Bars data={pivot(rows, 'month', 'country', 'new_outlets')} keys={[...COUNTRIES]} xFormat={monthLabel} />
        )}</WithData>
      </Card>
      <Card title="What kind of outlets lead?" sub={<>Share of leads by outlet type. Types come from a list of known outlets plus manual labels; “other” is not labelled yet.</>}>
        <CategoryPicker value={cat} onChange={setCat} withAll />
        <WithData d={types}>{(rows) => <StackedBars data={mixRows(rows, cat, 'outlet_type', TYPES, 'leads')} keys={TYPES} />}</WithData>
      </Card>
      <Card title="Domestic or foreign outlets?" sub="Share of leads by where the outlet is based (from its website or labels).">
        <CategoryPicker value={cat} onChange={setCat} withAll />
        <WithData d={origin}>{(rows) => <StackedBars data={mixRows(rows, cat, 'origin', ORIGINS, 'leads')} keys={ORIGINS} />}</WithData>
        <WithData d={cover}>{(rows) => (
          <p className="note">Labelled share of leads: {rows.map((r) => `${r.country} ${pct(r.leads_with_type)} (type), ${pct(r.leads_with_country)} (country)`).join(' · ')}</p>
        )}</WithData>
      </Card>
      <Card title="State-controlled media" sub="Outlets owned or directed by a government (outside public-service governance) seen in each edition.">
        <WithData d={state}>{(rows) => (
          <Table keyOf={(r) => `${r.country}${r.outlet}`} rows={rows} columns={[
            { label: 'Edition', left: true, render: (r: Row) => r.country },
            { label: 'Outlet', left: true, render: (r: Row) => r.outlet },
            { label: 'Country', render: (r: Row) => r.outlet_country },
            { label: 'Appearances', render: (r: Row) => int(r.appearances) },
            { label: 'Leads', render: (r: Row) => int(r.leads) },
            { label: 'Fair rate', render: (r: Row) => pct(r.fair_lead_rate) },
            { label: 'Sections', left: true, wrap: true, render: (r: Row) => r.sections },
          ]} />
        )}</WithData>
      </Card>
      <Card title="Which outlets appear together?" sub="The 40 outlets that appear most in each edition, linked when they often share story cards. Darker circles lead more often. Hover a circle to see its links.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={nodes}>{(ns) => (
          <WithData d={edges}>{(es) => (
            <Network
              nodes={ns.filter((n) => n.country === ed).map((n) => ({ id: n.outlet, size: n.appearances, rate: n.fair_lead_rate }))}
              edges={es.filter((e) => e.country === ed).map((e) => ({ source: e.source, target: e.target, strength: e.strength }))} />
          )}</WithData>
        )}</WithData>
      </Card>
      <OutletProfile />
    </>
  );
}

function OutletProfile() {
  const outlets = useData('profile_outlets');
  const monthly = useData('profile_monthly');
  const cats = useData('profile_categories');
  const partners = useData('profile_partners');
  const [ed, setEd] = useState('United States');
  const [q, setQ] = useState('');
  const options = useMemo(() => (outlets.data ?? []).filter((o) => o.country === ed).map((o) => o.outlet as string), [outlets.data, ed]);
  const name = options.find((o) => o.toLowerCase() === q.toLowerCase()) ?? options[0];
  const o = outlets.data?.find((r) => r.country === ed && r.outlet === name);
  return (
    <Card title="Outlet profile" sub="The 250 outlets that appear most in each edition.">
      <EditionPicker value={ed} onChange={(v) => { setEd(v); setQ(''); }} />
      <label className="picker">Outlet
        <input list="outlet-list" value={q} placeholder={name} onChange={(e) => setQ(e.target.value)} />
        <datalist id="outlet-list">{options.map((x) => <option key={x} value={x} />)}</datalist>
      </label>
      <WithData d={outlets}>{() => (o ? (
        <>
          <div className="stats">
            <div><b>{int(o.appearances)}</b><span>appearances</span></div>
            <div><b>{int(o.leads)}</b><span>leads</span></div>
            <div><b>{pct(o.lead_rate)}</b><span>lead rate</span></div>
            <div><b>{pct(o.fair_lead_rate)}</b><span>fair rate</span></div>
            <div><b>{o.first_seen}</b><span>first seen</span></div>
            <div><b>{o.website ? new URL(o.website).hostname.replace(/^www\./, '') : '—'}</b><span>website</span></div>
          </div>
          <div className="grid2">
            <div><h3>Month by month</h3>
              <WithData d={monthly}>{(rows) => {
                const m = rows.filter((r) => r.country === ed && r.outlet === name);
                return <Lines data={m.map((r) => ({ x: r.month, appearances: r.appearances, leads: r.leads }))}
                  keys={['appearances', 'leads']} xFormat={monthLabel} height={240} dots />;
              }}</WithData></div>
            <div><h3>Sections</h3>
              <WithData d={cats}>{(rows) => (
                <HBars rows={rows.filter((r) => r.country === ed && r.outlet === name)} label="category" value="appearances" />
              )}</WithData></div>
          </div>
          <h3>Often appears with</h3>
          <WithData d={partners}>{(rows) => (
            <p>{rows.filter((r) => r.country === ed && r.outlet === name).map((r) => `${r.partner} (${int(r.together)})`).join(' · ') || '—'}</p>
          )}</WithData>
        </>
      ) : <p className="note">No outlet selected.</p>)}</WithData>
    </Card>
  );
}
