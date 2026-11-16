import { Heatmap, StackedBars } from '../components/Plots';
import { Card, Table, WithData } from '../components/Ui';
import { COUNTRIES, Row, int, pct, pivot, toShares, useData } from '../data';

export default function Compare() {
  const sim = useData('world_edition_similarity');
  const across = useData('world_outlets_across_editions');
  const origin = useData('origin_mix');
  const evCov = useData('event_coverage');
  const shared = useData('shared_events');
  const evOrigin = useData('event_lead_origin');
  return (
    <>
      <Card title="Who leads World news: how alike are the editions?"
        sub="Overlap of the outlets leading World news between two editions: 0% = no outlet in common, 100% = the same outlets in the same proportions.">
        <WithData d={sim}>{(rows) => (
          <Heatmap rows={[...COUNTRIES]} cols={[...COUNTRIES]} format={(v) => pct(v)} max={1}
            value={(a, b) => (a === b ? null : rows.find((r) => r.edition_a === a && r.edition_b === b)?.overlap ?? 0)} />
        )}</WithData>
      </Card>
      <Card title="Domestic or foreign outlets in World news" sub="Share of World leads by where the outlet is based.">
        <WithData d={origin}>{(rows) => {
          const p = pivot(rows.filter((r) => r.category === 'World'), 'country', 'origin', 'leads');
          const ordered = COUNTRIES.map((c) => p.find((r) => r.x === c)).filter(Boolean) as Row[];
          return <StackedBars data={toShares(ordered, ['domestic', 'foreign', 'unknown'])} keys={['domestic', 'foreign', 'unknown']} />;
        }}</WithData>
      </Card>
      <Card title="Outlets that lead World news in several editions" sub="Matched by website. Share: the outlet's part of each edition's World leads.">
        <WithData d={across}>{(rows) => {
          const byDomain = new Map<string, Row>();
          for (const r of rows) {
            const o = byDomain.get(r.domain) ?? { outlet: r.outlet, domain: r.domain, editions_led: r.editions_led };
            o[r.country] = r.lead_share;
            byDomain.set(r.domain, o);
          }
          return <Table keyOf={(r) => String(r.domain)} rows={[...byDomain.values()]} columns={[
            { label: 'Outlet', left: true, render: (r: Row) => r.outlet },
            { label: 'Editions', render: (r: Row) => r.editions_led },
            ...COUNTRIES.map((c) => ({ label: c, render: (r: Row) => (r[c] == null ? '—' : pct(r[c], 1)) })),
          ]} />;
        }}</WithData>
      </Card>
      <Card title="Same event, how many editions?"
        sub="World and Politics stories matched across editions by headline meaning (multilingual model). Share of each edition's stories whose event is covered by 1, 2, 3 or all 4 editions.">
        <WithData d={evCov}>{(rows) => {
          const p = pivot(rows, 'country', 'editions', 'stories');
          const keys = ['1', '2', '3', '4'];
          const ordered = COUNTRIES.map((c) => p.find((r) => r.x === c)).filter(Boolean) as Row[];
          return <StackedBars data={toShares(ordered, keys)} keys={keys} />;
        }}</WithData>
        <WithData d={evOrigin}>{(rows) => (
          <p className="note">Of {int(rows.length)} events covered by all four editions, the same outlet leads everywhere in{' '}
            {pct(rows.filter((r) => r.same_outlet_everywhere).length / (rows.length || 1))} of them.</p>
        )}</WithData>
      </Card>
      <Card title="Events covered by the most editions" sub="Each edition's lead headline and outlet for the same event.">
        <WithData d={shared}>{(rows) => (
          <div className="events">
            {rows.slice(0, 20).map((e) => (
              <div className="event" key={e.event}>
                <div className="event-head">{e.first_date} · {e.editions} editions · {e.stories} stories</div>
                {COUNTRIES.filter((c) => e.by_edition[c]).map((c) => (
                  <div key={c} className="event-row"><b>{c}</b> <span>{e.by_edition[c].headline}</span> <i>{e.by_edition[c].outlet}</i></div>
                ))}
              </div>
            ))}
          </div>
        )}</WithData>
      </Card>
    </>
  );
}
