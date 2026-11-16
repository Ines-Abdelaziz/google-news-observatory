import { useMemo, useState } from 'react';
import { Bars, Heatmap, HBars, StackedArea } from '../components/Plots';
import { Card, EditionPicker, Picker, WithData } from '../components/Ui';
import { CATEGORIES, COUNTRIES, Row, dayLabel, pct, pivot, useData } from '../data';

export default function Agenda() {
  const mix = useData('section_mix_weekly');
  const kwWeek = useData('keywords_weekly');
  const kwAll = useData('keywords_overall');
  const names = useData('names_overall');
  const namesMonth = useData('names_monthly');
  const mentions = useData('country_mentions');
  const life = useData('story_lifespan');
  const overlap = useData('section_overlap');
  const [ed, setEd] = useState('United States');
  const weeks = useMemo(() => [...new Set((kwWeek.data ?? []).filter((r) => r.country === ed).map((r) => r.week as string))].sort(), [kwWeek.data, ed]);
  const [week, setWeek] = useState('');
  const wk = weeks.includes(week) ? week : weeks[weeks.length - 1] ?? '';
  const months = useMemo(() => [...new Set((namesMonth.data ?? []).filter((r) => r.country === ed).map((r) => r.month as string))].sort(), [namesMonth.data, ed]);
  const [month, setMonth] = useState('');
  const mo = months.includes(month) ? month : months[months.length - 1] ?? '';
  return (
    <>
      <EditionPicker value={ed} onChange={setEd} />
      <Card title="Section mix, week by week" sub="Share of each section in the edition's collected stories.">
        <WithData d={mix}>{(rows) => (
          <StackedArea data={pivot(rows.filter((r) => r.country === ed), 'week', 'category', 'stories')}
            keys={[...CATEGORIES]} shares xFormat={dayLabel} />
        )}</WithData>
      </Card>
      <Card title="What stood out each week" sub="Words and word pairs from lead headlines that were much more frequent that week than usual.">
        {weeks.length > 0 && (
          <Picker label="Week of" value={wk} options={weeks} onChange={setWeek} />
        )}
        <WithData d={kwWeek}>{(rows) => (
          <HBars rows={rows.filter((r) => r.country === ed && r.week === wk)} label="term" value="stories" />
        )}</WithData>
      </Card>
      <div className="grid2">
        <Card title="Most frequent words, whole period">
          <WithData d={kwAll}>{(rows) => <HBars rows={rows.filter((r) => r.country === ed).slice(0, 20)} label="term" value="stories" />}</WithData>
        </Card>
        <Card title="Most-mentioned names, whole period" sub="Capitalized word sequences in lead headlines: mostly people, parties and organizations.">
          <WithData d={names}>{(rows) => <HBars rows={rows.filter((r) => r.country === ed).slice(0, 20)} label="name" value="stories" />}</WithData>
        </Card>
      </div>
      <Card title="Most-mentioned names, one month">
        {months.length > 0 && <Picker label="Month" value={mo} options={months} onChange={setMonth} />}
        <WithData d={namesMonth}>{(rows) => <HBars rows={rows.filter((r) => r.country === ed && r.month === mo)} label="name" value="stories" />}</WithData>
      </Card>
      <Card title="Which countries World news is about" sub="Share of the edition's World headlines that name each country.">
        <WithData d={mentions}>{(rows) => (
          <HBars rows={rows.filter((r) => r.country === ed).slice(0, 20)} label="mentioned" value="share" format={(v) => pct(v, 1)} />
        )}</WithData>
      </Card>
      <div className="grid2">
        <Card title="How long a lead article stays" sub="Days the same lead article is seen in the same section (7 = a week or more).">
          <WithData d={life}>{(rows) => {
            const tot = Object.fromEntries(COUNTRIES.map((c) => [c, rows.filter((r) => r.country === c).reduce((s, r) => s + r.stories, 0)]));
            return <Bars data={pivot(rows, 'days', 'country', (r: Row) => r.stories / (tot[r.country] || 1))}
              keys={[...COUNTRIES]} format={(v) => pct(v)} />;
          }}</WithData>
        </Card>
        <Card title="Stories filed in two sections" sub="Of a row section's stories, the share also filed under the column section the same day.">
          <WithData d={overlap}>{(rows) => {
            const r = rows.filter((x) => x.country === ed);
            return <Heatmap rows={[...CATEGORIES]} cols={[...CATEGORIES]} format={(v) => pct(v)}
              colLabel={(c) => c.slice(0, 4)}
              value={(a, b) => (a === b ? null : r.find((x) => x.category_a === a && x.category_b === b)?.share_of_a ?? 0)} />;
          }}</WithData>
        </Card>
      </div>
    </>
  );
}
