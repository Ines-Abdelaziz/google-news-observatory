-- Aggregates the site reads. Materialized: refresh after each load
-- (load_db.py does it). Shares are 0..1. "fair" columns count only stories
-- with at least 2 outlets, where the lead is a real choice by Google.

DROP MATERIALIZED VIEW IF EXISTS mv_top_outlets, mv_top_outlets_by_category, mv_category_overview,
    mv_kpi, mv_concentration_monthly, mv_coverage_daily, mv_sources_by_category, mv_sources CASCADE;

CREATE MATERIALIZED VIEW mv_sources AS
SELECT e.label AS country, i.outlet,
       count(*)                                                        AS appearances,
       count(*) FILTER (WHERE i.position = 0)                          AS leads,
       count(*) FILTER (WHERE s.cluster_size >= 2)                     AS multi_appearances,
       count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)  AS multi_leads,
       round(count(*) FILTER (WHERE i.position = 0)::numeric / count(*), 4)::float8 AS lead_rate,
       round(count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)::numeric
             / nullif(count(*) FILTER (WHERE s.cluster_size >= 2), 0), 4)::float8   AS fair_lead_rate,
       min(s.file_date) AS first_seen, max(s.file_date) AS last_seen,
       mode() WITHIN GROUP (ORDER BY s.lead_website) FILTER (WHERE i.position = 0) AS website
FROM cluster_items i
JOIN stories s USING (story_id)
JOIN editions e ON e.country = s.country
WHERE i.outlet <> ''
GROUP BY e.label, i.outlet;

CREATE MATERIALIZED VIEW mv_sources_by_category AS
SELECT e.label AS country, s.category, i.outlet,
       count(*)                                                        AS appearances,
       count(*) FILTER (WHERE i.position = 0)                          AS leads,
       count(*) FILTER (WHERE s.cluster_size >= 2)                     AS multi_appearances,
       count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)  AS multi_leads
FROM cluster_items i
JOIN stories s USING (story_id)
JOIN editions e ON e.country = s.country
WHERE i.outlet <> ''
GROUP BY e.label, s.category, i.outlet;

CREATE MATERIALIZED VIEW mv_kpi AS
WITH st AS (
    SELECT e.label AS country, e.sort, count(*) AS stories, count(DISTINCT s.file_date) AS days,
           min(s.file_date) AS first_date, max(s.file_date) AS last_date,
           avg((s.cluster_size = 1)::int) AS single_share
    FROM stories s JOIN editions e ON e.country = s.country
    GROUP BY e.label, e.sort
), ranked AS (
    SELECT country, leads, row_number() OVER (PARTITION BY country ORDER BY leads DESC) AS rk
    FROM mv_sources
)
SELECT st.country, st.stories, st.days, st.first_date, st.last_date,
       (SELECT count(*) FROM mv_sources m WHERE m.country = st.country)                AS outlets,
       (SELECT count(*) FROM mv_sources m WHERE m.country = st.country AND leads > 0)  AS lead_outlets,
       round((SELECT sum(leads) FROM ranked r WHERE r.country = st.country AND rk <= 10)::numeric
             / st.stories, 4)::float8 AS top10_share,
       round(st.single_share, 4)::float8 AS single_share
FROM st
ORDER BY st.sort;

CREATE MATERIALIZED VIEW mv_concentration_monthly AS
WITH leads AS (
    SELECT e.label AS country, to_char(s.file_date, 'YYYY-MM') AS month, s.category, s.lead_outlet AS outlet
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.lead_outlet <> ''
), counts AS (
    SELECT country, month, category, outlet, count(*) AS n FROM leads GROUP BY 1, 2, 3, 4
    UNION ALL
    SELECT country, month, 'All', outlet, count(*) FROM leads GROUP BY 1, 2, 4
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY country, month, category ORDER BY n DESC) AS rk,
           sum(n) OVER (PARTITION BY country, month, category) AS total
    FROM counts
)
SELECT country, month, category,
       max(total)::int AS stories,
       count(*)        AS lead_outlets,
       round(sum(n) FILTER (WHERE rk <= 10)::numeric / max(total), 4)::float8 AS top10_share,
       round(sum((n::numeric / total) ^ 2), 5)::float8                        AS hhi
FROM ranked
GROUP BY country, month, category;

CREATE MATERIALIZED VIEW mv_category_overview AS
WITH st AS (
    SELECT e.label AS country, s.category, count(*) AS stories, avg((s.cluster_size = 1)::int) AS single_share
    FROM stories s JOIN editions e ON e.country = s.country
    GROUP BY 1, 2
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY country, category ORDER BY leads DESC, outlet) AS rk
    FROM mv_sources_by_category
)
SELECT st.country, st.category, st.stories,
       count(r.*)                              AS outlets,
       count(r.*) FILTER (WHERE r.leads > 0)  AS lead_outlets,
       round(sum(r.leads) FILTER (WHERE r.rk <= 10)::numeric / st.stories, 4)::float8 AS top10_share,
       round(st.single_share, 4)::float8       AS single_share,
       max(r.outlet) FILTER (WHERE r.rk = 1)   AS top_outlet,
       round(max(r.leads) FILTER (WHERE r.rk = 1)::numeric / st.stories, 4)::float8 AS top_outlet_share
FROM st
JOIN ranked r ON r.country = st.country AND r.category = st.category
GROUP BY st.country, st.category, st.stories, st.single_share;

CREATE MATERIALIZED VIEW mv_top_outlets AS
SELECT country, outlet, website, leads, appearances, lead_rate, fair_lead_rate,
       round(leads::numeric / all_leads, 4)::float8 AS lead_share
FROM (
    SELECT m.*, sum(leads) OVER (PARTITION BY country) AS all_leads,
           row_number() OVER (PARTITION BY country ORDER BY leads DESC, outlet) AS rk
    FROM mv_sources m
) x
WHERE rk <= 15;

CREATE MATERIALIZED VIEW mv_top_outlets_by_category AS
SELECT country, category, outlet, leads, appearances,
       round(leads::numeric / appearances, 4)::float8 AS lead_rate,
       round(multi_leads::numeric / nullif(multi_appearances, 0), 4)::float8 AS fair_lead_rate,
       round(leads::numeric / all_leads, 4)::float8 AS lead_share
FROM (
    SELECT m.*, sum(leads) OVER (PARTITION BY country, category) AS all_leads,
           row_number() OVER (PARTITION BY country, category ORDER BY leads DESC, outlet) AS rk
    FROM mv_sources_by_category m
) x
WHERE rk <= 10;

CREATE MATERIALIZED VIEW mv_coverage_daily AS
SELECT e.label AS country, c.date, sum(c.n_stories)::int AS stories
FROM coverage c JOIN editions e ON e.country = c.country
GROUP BY e.label, c.date;
