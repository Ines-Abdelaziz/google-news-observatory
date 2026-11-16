-- Aggregates that need outlet labels (table outlet_labels, built by gnobs/labels.py).

-- how much of each edition's lead slot is labelled, and how (label quality)
CREATE TABLE label_coverage AS
SELECT s.country,
       round(sum(s.leads) FILTER (WHERE l.origin <> 'unknown') / sum(s.leads), 4)                 AS leads_with_country,
       round(sum(s.leads) FILTER (WHERE l.country_source IN ('manual', 'known')) / sum(s.leads), 4) AS leads_country_checked,
       round(sum(s.leads) FILTER (WHERE l.type_source IN ('manual', 'known')) / sum(s.leads), 4)    AS leads_type_checked,
       round(coalesce(sum(s.leads) FILTER (WHERE l.leaning <> 'unknown'), 0) / sum(s.leads), 4)   AS leads_with_leaning
FROM sources s JOIN outlet_labels l USING (country, outlet)
GROUP BY s.country ORDER BY s.country;

-- political leaning of the outlets leading each edition (where a rating exists)
CREATE TABLE leaning_mix AS
WITH b AS (
    SELECT c.country, c.category, l.leaning, c.appearances, c.leads
    FROM sources_by_category c JOIN outlet_labels l USING (country, outlet)
)
SELECT country, category, leaning, sum(appearances) AS appearances, sum(leads) AS leads FROM b GROUP BY ALL
UNION ALL
SELECT country, 'All', leaning, sum(appearances), sum(leads) FROM b GROUP BY country, leaning
ORDER BY country, category, leaning;

-- every outlet seen, with its labels (published as a downloadable CSV)
CREATE TABLE all_outlets AS
SELECT s.country AS edition, s.outlet, l.domain, l.outlet_country, l.country_source, l.outlet_type, l.type_source,
       l.origin, l.leaning, l.leaning_source, s.appearances, s.leads, s.lead_rate, s.fair_lead_rate,
       s.first_seen, s.last_seen
FROM sources s JOIN outlet_labels l USING (country, outlet)
ORDER BY s.country, s.appearances DESC;

-- domestic vs foreign outlets, per section (and All)
CREATE TABLE origin_mix AS
WITH b AS (
    SELECT c.country, c.category, l.origin, c.appearances, c.leads, c.multi_leads
    FROM sources_by_category c JOIN outlet_labels l USING (country, outlet)
)
SELECT country, category, origin, sum(appearances) AS appearances, sum(leads) AS leads FROM b GROUP BY ALL
UNION ALL
SELECT country, 'All', origin, sum(appearances), sum(leads) FROM b GROUP BY country, origin
ORDER BY country, category, origin;

-- outlet types, per section (and All)
CREATE TABLE type_mix AS
WITH b AS (
    SELECT c.country, c.category, l.outlet_type, c.appearances, c.leads
    FROM sources_by_category c JOIN outlet_labels l USING (country, outlet)
)
SELECT country, category, outlet_type, sum(appearances) AS appearances, sum(leads) AS leads FROM b GROUP BY ALL
UNION ALL
SELECT country, 'All', outlet_type, sum(appearances), sum(leads) FROM b GROUP BY country, outlet_type
ORDER BY country, category, outlet_type;

-- state-controlled outlets seen in each edition
CREATE TABLE state_media AS
SELECT s.country, s.outlet, l.outlet_country, s.appearances, s.leads, s.fair_lead_rate, s.first_seen, s.last_seen,
       (SELECT string_agg(category, ', ' ORDER BY appearances DESC) FROM sources_by_category c
        WHERE c.country = s.country AND c.outlet = s.outlet) AS sections
FROM sources s JOIN outlet_labels l USING (country, outlet)
WHERE l.outlet_type = 'state-controlled'
ORDER BY s.country, s.appearances DESC;

-- foreign outlets leading World news in the most editions (matched by website domain)
CREATE TABLE world_outlets_across_editions AS
WITH w AS (
    SELECT c.country, l.domain, c.outlet, c.leads, c.appearances,
           c.leads / sum(c.leads) OVER (PARTITION BY c.country) AS lead_share
    FROM sources_by_category c JOIN outlet_labels l USING (country, outlet)
    WHERE c.category = 'World' AND l.domain <> ''
), d AS (
    SELECT domain, count(DISTINCT country) FILTER (WHERE leads > 0) AS editions_led,
           arg_max(outlet, leads) AS outlet, sum(leads) AS total_leads
    FROM w GROUP BY domain
)
SELECT d.outlet, d.domain, d.editions_led, w.country, sum(w.leads) AS leads, round(sum(w.lead_share), 4) AS lead_share
FROM d JOIN w USING (domain)
WHERE d.editions_led >= 2
GROUP BY ALL
ORDER BY d.editions_led DESC, d.domain, w.country;

-- how alike two editions are in who leads their World news (0 = no overlap, 1 = identical)
CREATE TABLE world_edition_similarity AS
WITH w AS (
    SELECT c.country, l.domain, sum(c.leads) AS leads
    FROM sources_by_category c JOIN outlet_labels l USING (country, outlet)
    WHERE c.category = 'World' AND l.domain <> ''
    GROUP BY ALL
), s AS (SELECT *, leads / sum(leads) OVER (PARTITION BY country) AS share FROM w),
e AS (SELECT DISTINCT country FROM s)
SELECT a.country AS edition_a, b.country AS edition_b,
       round(coalesce((SELECT sum(least(x.share, y.share)) FROM s x JOIN s y USING (domain)
                       WHERE x.country = a.country AND y.country = b.country), 0), 4) AS overlap
FROM e a CROSS JOIN e b
ORDER BY 1, 2;

-- top outlets with their labels, to check and correct (written as CSV, not shown on the site)
CREATE TABLE labels_review AS
SELECT s.country, s.outlet, l.domain, l.outlet_country, l.country_source, l.outlet_type, l.type_source,
       l.origin, l.leaning, l.leaning_source, s.appearances, s.leads
FROM sources s JOIN outlet_labels l USING (country, outlet)
QUALIFY row_number() OVER (PARTITION BY s.country ORDER BY s.appearances DESC) <= 300
ORDER BY s.country, s.appearances DESC;
