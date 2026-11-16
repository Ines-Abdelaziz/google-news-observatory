import { useState } from 'react';
import { CoverageChart, ConcentrationChart } from './components/Charts';
import { CategoryMatrix, CategoryOverview, KpiTable, OutletTables } from './components/Tables';
import { CATEGORIES, CategoryRow, DayRow, Kpi, MonthConc, OutletRow, int, pct, useData } from './data';

export default function App() {
  const kpi = useData<Kpi[]>('kpi');
  const conc = useData<MonthConc[]>('concentration_monthly');
  const cats = useData<CategoryRow[]>('category_overview');
  const catTop = useData<OutletRow[]>('top_outlets_by_category');
  const top = useData<OutletRow[]>('top_outlets');
  const cov = useData<DayRow[]>('coverage_daily');
  const [cat, setCat] = useState<string>('Politics');

  const most = kpi && [...kpi].sort((a, b) => b.top10_share - a.top10_share)[0];
  const least = kpi && [...kpi].sort((a, b) => a.top10_share - b.top10_share)[0];

  return (
    <main>
      <header>
        <h1>Google News: who gets the lead slot?</h1>
        <p className="lede">
          When several outlets cover a story, Google News shows one as the lead and a few others underneath.{' '}
          {most && least ? (
            <>
              <b>{most.country}</b> has the most concentrated lead slot: its 10 most-credited outlets lead{' '}
              <b>{pct(most.top10_share)}</b> of stories, against <b>{pct(least.top10_share)}</b> in{' '}
              <b>{least.country}</b>.
            </>
          ) : '…'}
        </p>
        <p className="sub">
          Daily snapshots of the non-personalized Google News topic feeds (World, Nation, Politics, Business,
          Technology, Science, Health) in four country editions
          {kpi ? `, ${int(kpi.reduce((s, r) => s + r.stories, 0))} stories` : ''}.
        </p>
      </header>

      <section className="card">
        <h2>Overview by country edition</h2>
        <p className="sub">Top-10 share: share of all stories whose lead comes from the edition's 10 most-credited outlets.</p>
        {kpi ? <KpiTable rows={kpi} /> : <p>Loading…</p>}
      </section>

      <section className="card">
        <h2>Top-10 share of the lead slot, by month</h2>
        <p className="sub">All categories together. The European editions start in March 2026.</p>
        {conc ? <ConcentrationChart rows={conc} /> : <p>Loading…</p>}
      </section>

      <section className="card">
        <h2>Stories by category</h2>
        {cats ? <CategoryMatrix rows={cats} value={(r) => r.stories} format={int} /> : <p>Loading…</p>}
        <h2 className="spaced">Top-10 share by category</h2>
        <p className="sub">Darker: a few outlets take more of the lead slot.</p>
        {cats ? <CategoryMatrix rows={cats} value={(r) => r.top10_share} format={(v) => pct(v)} /> : <p>Loading…</p>}
      </section>

      <section className="card">
        <h2>One category in detail</h2>
        <label className="picker">
          Category{' '}
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        {cats ? <CategoryOverview rows={cats.filter((r) => r.category === cat)} /> : <p>Loading…</p>}
        <h3 className="spaced">Top 10 outlets in {cat}</h3>
        {catTop ? <OutletTables rows={catTop.filter((r) => r.category === cat)} /> : <p>Loading…</p>}
      </section>

      <section className="card">
        <h2>Most-credited outlets, all categories</h2>
        <p className="sub">
          Leads: stories where the outlet is the lead. Lead rate: leads ÷ all its appearances in story clusters. Fair rate: the same, counting only stories with at least two outlets, where the lead is a real choice.
          Share: its part of all the edition's leads.
        </p>
        {top ? <OutletTables rows={top} /> : <p>Loading…</p>}
      </section>

      <section className="card">
        <h2>Stories collected per day</h2>
        <p className="sub">Gaps are days when the collector got nothing back.</p>
        {cov ? <CoverageChart rows={cov} /> : <p>Loading…</p>}
      </section>

      <details>
        <summary>How to read these numbers</summary>
        <ul>
          <li>Each story is one card from a Google News topic feed: one lead article plus up to four related articles from other outlets.</li>
          <li>Feeds are the non-personalized country editions, collected once a day: they show Google's editorial choices, not what any individual reader saw.</li>
          <li>Single-article stories have only one outlet, which leads by default; this raises the lead rate of outlets that often publish alone.</li>
          <li>Outlet names are taken as Google writes them, so one outlet can appear under two names, and aggregators are counted as outlets.</li>
        </ul>
      </details>
    </main>
  );
}
