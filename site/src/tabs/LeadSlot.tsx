import { useState } from 'react';
import { Heatmap, Lines } from '../components/Plots';
import { Card, CategoryPicker, EditionPicker, Table, WithData } from '../components/Ui';
import { CATEGORIES, COUNTRIES, Row, int, monthLabel, pct, pivot, useData } from '../data';

const outletCols = [
  { label: 'Outlet', left: true, wrap: true, render: (r: Row) => r.outlet },
  { label: 'Leads', render: (r: Row) => int(r.leads) },
  { label: 'Lead rate', render: (r: Row) => pct(r.lead_rate) },
  { label: 'Fair rate', render: (r: Row) => pct(r.fair_lead_rate) },
  { label: 'Share', render: (r: Row) => pct(r.lead_share, 1) },
];

export default function LeadSlot() {
  const cats = useData('category_overview');
  const conc = useData('concentration_monthly');
  const catTop = useData('top_outlets_by_category');
  const top = useData('top_outlets');
  const pos = useData('feed_position');
  const style = useData('headline_style');
  const lvr = useData('lead_vs_related_headlines');
  const [cat, setCat] = useState('Politics');
  const [ed, setEd] = useState('United States');
  return (
    <>
      <p className="lede">
        <b>Leads</b>: stories where the outlet's article is on top. <b>Lead rate</b>: leads ÷ all the story cards
        the outlet appears in. <b>Fair rate</b>: the same, counting only cards with at least two outlets, where
        Google actually had a choice. <b>Share</b>: the outlet's part of all the edition's leads.
      </p>
      <Card title="Concentration by section" sub="Share of each section's stories led by its 10 most-credited outlets, over the whole period.">
        <WithData d={cats}>{(rows) => (
          <Heatmap rows={[...CATEGORIES]} cols={[...COUNTRIES]} format={(v) => pct(v)} max={1}
            value={(r, c) => rows.find((x) => x.category === r && x.country === c)?.top10_share ?? null} />
        )}</WithData>
      </Card>
      <Card title="Concentration over time, one section">
        <CategoryPicker value={cat} onChange={setCat} withAll />
        <WithData d={conc}>{(rows) => (
          <Lines data={pivot(rows.filter((r) => r.category === cat), 'month', 'country', 'top10_share')}
            keys={[...COUNTRIES]} yFormat={(v) => pct(v)} xFormat={monthLabel} yDomain={[0, 1]} dots />
        )}</WithData>
      </Card>
      <Card title="Most-credited outlets in one section">
        <CategoryPicker value={cat === 'All' ? 'Politics' : cat} onChange={setCat} />
        <WithData d={cats}>{(rows) => (
          <Table keyOf={(r) => String(r.country)} rows={COUNTRIES.map((c) => rows.find((r) => r.country === c && r.category === (cat === 'All' ? 'Politics' : cat))).filter(Boolean) as Row[]}
            columns={[
              { label: 'Edition', left: true, render: (r: Row) => r.country },
              { label: 'Stories', render: (r: Row) => int(r.stories) },
              { label: 'Outlets seen', render: (r: Row) => int(r.outlets) },
              { label: 'Top-10 share', render: (r: Row) => pct(r.top10_share) },
              { label: 'Single-article', render: (r: Row) => pct(r.single_share) },
              { label: 'Top outlet', left: true, render: (r: Row) => r.top_outlet },
              { label: 'Its share', render: (r: Row) => pct(r.top_outlet_share, 1) },
            ]} />
        )}</WithData>
        <WithData d={catTop}>{(rows) => (
          <div className="grid4">
            {COUNTRIES.map((c) => (
              <div key={c}><h3>{c}</h3>
                <Table keyOf={(r) => String(r.outlet)} columns={outletCols}
                  rows={rows.filter((r) => r.country === c && r.category === (cat === 'All' ? 'Politics' : cat))} />
              </div>
            ))}
          </div>
        )}</WithData>
      </Card>
      <Card title="Most-credited outlets, all sections">
        <WithData d={top}>{(rows) => (
          <div className="grid4">
            {COUNTRIES.map((c) => (
              <div key={c}><h3>{c}</h3>
                <Table keyOf={(r) => String(r.outlet)} columns={outletCols} rows={rows.filter((r) => r.country === c)} />
              </div>
            ))}
          </div>
        )}</WithData>
      </Card>
      <Card title="Who gets the first slots of the feed?"
        sub="Share of all leads vs share of the leads in the first 5 positions of each daily section feed. Positions come from the order of the collected feed.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={pos}>{(rows) => (
          <Table keyOf={(r) => String(r.outlet)} rows={rows.filter((r) => r.country === ed)} columns={[
            { label: 'Outlet', left: true, wrap: true, render: (r: Row) => r.outlet },
            { label: 'Leads', render: (r: Row) => int(r.leads) },
            { label: 'Share of all leads', render: (r: Row) => pct(r.share_all, 1) },
            { label: 'Share of top-5 leads', render: (r: Row) => pct(r.share_top5, 1) },
            { label: 'Ratio', render: (r: Row) => (r.share_all ? (r.share_top5 / r.share_all).toFixed(2) : '—') },
          ]} />
        )}</WithData>
      </Card>
      <Card title="Do lead headlines look different?" sub="Headlines of lead articles vs the related articles underneath them, in story cards with at least two outlets.">
        <WithData d={lvr}>{(rows) => (
          <Table keyOf={(r) => `${r.country}${r.role}`} rows={rows} columns={[
            { label: 'Edition', left: true, render: (r: Row) => r.country },
            { label: 'Role', left: true, render: (r: Row) => r.role },
            { label: 'Characters', render: (r: Row) => r.avg_chars },
            { label: 'Words', render: (r: Row) => r.avg_words },
            { label: 'Questions', render: (r: Row) => pct(r.question_share, 1) },
            { label: 'Numbers', render: (r: Row) => pct(r.number_share, 1) },
            { label: 'Quotes', render: (r: Row) => pct(r.quote_share, 1) },
            { label: 'Colons', render: (r: Row) => pct(r.colon_share, 1) },
            { label: '!', render: (r: Row) => pct(r.exclaim_share, 1) },
          ]} />
        )}</WithData>
      </Card>
      <Card title="Headline style of the most-credited outlets" sub="Lead headlines only.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={style}>{(rows) => (
          <Table keyOf={(r) => String(r.outlet)} rows={rows.filter((r) => r.country === ed)} columns={[
            { label: 'Outlet', left: true, wrap: true, render: (r: Row) => r.outlet },
            { label: 'Headlines', render: (r: Row) => int(r.headlines) },
            { label: 'Characters', render: (r: Row) => r.avg_chars },
            { label: 'Questions', render: (r: Row) => pct(r.question_share, 1) },
            { label: 'Numbers', render: (r: Row) => pct(r.number_share, 1) },
            { label: 'Quotes', render: (r: Row) => pct(r.quote_share, 1) },
            { label: 'Colons', render: (r: Row) => pct(r.colon_share, 1) },
          ]} />
        )}</WithData>
      </Card>
    </>
  );
}
