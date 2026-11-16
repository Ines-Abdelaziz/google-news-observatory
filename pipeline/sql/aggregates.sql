-- Aggregates the website reads, computed with DuckDB from the build_tables outputs.
-- Inputs (views created by export_json.py): stories, cluster_items, coverage, editions.
-- Shares are 0..1. "fair" columns count only stories with at least 2 outlets,
-- where the lead is a real choice by Google.

CREATE TABLE sources AS
SELECT e.label AS country, i.outlet,
       count(*)                                                        AS appearances,
       count(*) FILTER (WHERE i.position = 0)                          AS leads,
       count(*) FILTER (WHERE s.cluster_size >= 2)                     AS multi_appearances,
       count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)  AS multi_leads,
       round(count(*) FILTER (WHERE i.position = 0) / count(*), 4)     AS lead_rate,
       round(count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)
             / nullif(count(*) FILTER (WHERE s.cluster_size >= 2), 0), 4) AS fair_lead_rate,
       min(s.file_date) AS first_seen, max(s.file_date) AS last_seen,
       mode(s.lead_website) FILTER (WHERE i.position = 0)              AS website
FROM cluster_items i
JOIN stories s USING (story_id)
JOIN editions e ON e.country = s.country
WHERE i.outlet <> ''
GROUP BY ALL;

CREATE TABLE sources_by_category AS
SELECT e.label AS country, s.category, i.outlet,
       count(*)                                                        AS appearances,
       count(*) FILTER (WHERE i.position = 0)                          AS leads,
       count(*) FILTER (WHERE s.cluster_size >= 2)                     AS multi_appearances,
       count(*) FILTER (WHERE s.cluster_size >= 2 AND i.position = 0)  AS multi_leads
FROM cluster_items i
JOIN stories s USING (story_id)
JOIN editions e ON e.country = s.country
WHERE i.outlet <> ''
GROUP BY ALL;

CREATE TABLE kpi AS
WITH st AS (
    SELECT e.label AS country, e.sort, count(*) AS stories, count(DISTINCT s.file_date) AS days,
           min(s.file_date) AS first_date, max(s.file_date) AS last_date,
           avg((s.cluster_size = 1)::INT) AS single_share
    FROM stories s JOIN editions e ON e.country = s.country
    GROUP BY ALL
), ranked AS (
    SELECT country, leads, row_number() OVER (PARTITION BY country ORDER BY leads DESC) AS rk FROM sources
), per AS (
    SELECT country, count(*) AS outlets, count(*) FILTER (WHERE leads > 0) AS lead_outlets FROM sources GROUP BY ALL
), top10 AS (
    SELECT country, sum(leads) AS top10_leads FROM ranked WHERE rk <= 10 GROUP BY ALL
)
SELECT st.country, st.stories, st.days, st.first_date, st.last_date, per.outlets, per.lead_outlets,
       round(top10.top10_leads / st.stories, 4) AS top10_share,
       round(st.single_share, 4) AS single_share
FROM st JOIN per USING (country) JOIN top10 USING (country)
ORDER BY st.sort;

CREATE TABLE concentration_monthly AS
WITH leads AS (
    SELECT e.label AS country, strftime(s.file_date, '%Y-%m') AS month, s.category, s.lead_outlet AS outlet
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.lead_outlet <> ''
), counts AS (
    SELECT country, month, category, outlet, count(*) AS n FROM leads GROUP BY ALL
    UNION ALL
    SELECT country, month, 'All' AS category, outlet, count(*) AS n FROM leads GROUP BY country, month, outlet
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY country, month, category ORDER BY n DESC) AS rk,
           sum(n) OVER (PARTITION BY country, month, category) AS total
    FROM counts
)
SELECT country, month, category,
       max(total)::INT AS stories,
       count(*)        AS lead_outlets,
       round(sum(n) FILTER (WHERE rk <= 10) / max(total), 4) AS top10_share,
       round(sum(pow(n / total, 2)), 5)                      AS hhi
FROM ranked
GROUP BY ALL
ORDER BY country, category, month;

CREATE TABLE category_overview AS
WITH st AS (
    SELECT e.label AS country, s.category, count(*) AS stories, avg((s.cluster_size = 1)::INT) AS single_share
    FROM stories s JOIN editions e ON e.country = s.country
    GROUP BY ALL
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY country, category ORDER BY leads DESC, outlet) AS rk
    FROM sources_by_category
)
SELECT st.country, st.category, st.stories,
       count(r.outlet)                              AS outlets,
       count(r.outlet) FILTER (WHERE r.leads > 0)   AS lead_outlets,
       round(sum(r.leads) FILTER (WHERE r.rk <= 10) / st.stories, 4) AS top10_share,
       round(st.single_share, 4)                    AS single_share,
       max(r.outlet) FILTER (WHERE r.rk = 1)        AS top_outlet,
       round(max(r.leads) FILTER (WHERE r.rk = 1) / st.stories, 4) AS top_outlet_share
FROM st
JOIN ranked r ON r.country = st.country AND r.category = st.category
GROUP BY st.country, st.category, st.stories, st.single_share
ORDER BY st.category, st.country;

CREATE TABLE top_outlets AS
SELECT country, outlet, website, leads, appearances, lead_rate, fair_lead_rate,
       round(leads / all_leads, 4) AS lead_share
FROM (
    SELECT *, sum(leads) OVER (PARTITION BY country) AS all_leads,
           row_number() OVER (PARTITION BY country ORDER BY leads DESC, outlet) AS rk
    FROM sources
)
WHERE rk <= 15
ORDER BY country, leads DESC;

CREATE TABLE top_outlets_by_category AS
SELECT country, category, outlet, leads, appearances,
       round(leads / appearances, 4) AS lead_rate,
       round(multi_leads / nullif(multi_appearances, 0), 4) AS fair_lead_rate,
       round(leads / all_leads, 4) AS lead_share
FROM (
    SELECT *, sum(leads) OVER (PARTITION BY country, category) AS all_leads,
           row_number() OVER (PARTITION BY country, category ORDER BY leads DESC, outlet) AS rk
    FROM sources_by_category
)
WHERE rk <= 10
ORDER BY country, category, leads DESC;

CREATE TABLE coverage_daily AS
SELECT e.label AS country, c.date, sum(c.n_stories)::INT AS stories
FROM coverage c JOIN editions e ON e.country = c.country
GROUP BY ALL
ORDER BY country, date;
