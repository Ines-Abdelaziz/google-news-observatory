import { Lines } from '../components/Plots';
import { Card, Table, WithData } from '../components/Ui';
import { COUNTRIES, Row, int, monthLabel, pct, pivot, useData } from '../data';

export default function Overview() {
  const kpi = useData('kpi');
  const conc = useData('concentration_monthly');
  const most = kpi.data && [...kpi.data].sort((a, b) => b.top10_share - a.top10_share)[0];
  const least = kpi.data && [...kpi.data].sort((a, b) => a.top10_share - b.top10_share)[0];
  return (
    <>
      <p className="lede">
        When several outlets cover a story, Google News shows one article as the <b>lead</b> and a few others
        underneath. This observatory tracks those choices every day in four editions of Google News.{' '}
        {most && least && (
          <>
            <b>{most.country}</b> has the most concentrated lead slot: its 10 most-credited outlets lead{' '}
            <b>{pct(most.top10_share)}</b> of stories, against <b>{pct(least.top10_share)}</b> in <b>{least.country}</b>.
          </>
        )}
      </p>
      <Card title="The four editions" sub="Top-10 share: share of all stories led by the edition's 10 most-credited outlets.">
        <WithData d={kpi}>{(rows) => (
          <Table keyOf={(r) => String(r.country)} rows={rows} columns={[
            { label: 'Edition', left: true, render: (r: Row) => r.country },
            { label: 'Stories', render: (r: Row) => int(r.stories) },
            { label: 'Days', render: (r: Row) => int(r.days) },
            { label: 'Since', render: (r: Row) => r.first_date },
            { label: 'Outlets seen', render: (r: Row) => int(r.outlets) },
            { label: 'Outlets that ever lead', render: (r: Row) => int(r.lead_outlets) },
            { label: 'Top-10 share', render: (r: Row) => pct(r.top10_share) },
            { label: 'Single-article stories', render: (r: Row) => pct(r.single_share) },
          ]} />
        )}</WithData>
      </Card>
      <Card title="Concentration of the lead slot, by month" sub="Share of stories led by each edition's 10 most-credited outlets that month, all sections together.">
        <WithData d={conc}>{(rows) => (
          <Lines data={pivot(rows.filter((r) => r.category === 'All'), 'month', 'country', 'top10_share')}
            keys={[...COUNTRIES]} yFormat={(v) => pct(v)} xFormat={monthLabel} yDomain={[0, 1]} dots />
        )}</WithData>
      </Card>
    </>
  );
}
