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

-- =====================================================================
-- Agenda: what gets covered
-- =====================================================================

-- stories per section per week (section mix over time)
CREATE TABLE section_mix_weekly AS
SELECT e.label AS country, date_trunc('week', s.file_date)::DATE AS week, s.category, count(*) AS stories
FROM stories s JOIN editions e ON e.country = s.country
GROUP BY ALL ORDER BY country, week, category;

-- how many days the same lead article stays in a section (same Google News link)
CREATE TABLE story_lifespan AS
WITH per_url AS (
    SELECT e.label AS country, s.category, s.url, count(DISTINCT s.file_date) AS days
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.url IS NOT NULL AND s.url <> ''
    GROUP BY ALL
)
SELECT country, least(days, 7) AS days, count(*) AS stories   -- 7 = "7 days or more"
FROM per_url GROUP BY ALL ORDER BY country, days;

-- the same lead article filed under several sections on the same day
CREATE TABLE section_overlap AS
WITH s2 AS (
    SELECT DISTINCT e.label AS country, s.file_date, s.url, s.category
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.url IS NOT NULL AND s.url <> ''
), sizes AS (
    SELECT country, category, count(*) AS n FROM s2 GROUP BY ALL
)
SELECT a.country, a.category AS category_a, b.category AS category_b, count(*) AS shared,
       round(count(*) / any_value(sa.n), 4) AS share_of_a
FROM s2 a
JOIN s2 b ON a.country = b.country AND a.file_date = b.file_date AND a.url = b.url AND a.category <> b.category
JOIN sizes sa ON sa.country = a.country AND sa.category = a.category
GROUP BY ALL ORDER BY a.country, a.category, b.category;

-- =====================================================================
-- Outlet ecosystem: who covers it
-- =====================================================================

-- distinct outlets appearing / leading per week
CREATE TABLE outlet_diversity_weekly AS
SELECT e.label AS country, date_trunc('week', s.file_date)::DATE AS week,
       count(DISTINCT i.outlet) AS outlets,
       count(DISTINCT i.outlet) FILTER (WHERE i.position = 0) AS lead_outlets,
       count(DISTINCT s.story_id) AS stories
FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
WHERE i.outlet <> ''
GROUP BY ALL ORDER BY country, week;

-- outlets seen for the first time / for the last time each month
-- (the first month of each edition and the last month overall are left out: every outlet would count)
CREATE TABLE outlet_churn_monthly AS
WITH bounds AS (
    SELECT country, strftime(min(first_seen), '%Y-%m') AS m0, strftime(max(last_seen), '%Y-%m') AS m1
    FROM sources GROUP BY country
), firsts AS (
    SELECT country, strftime(first_seen, '%Y-%m') AS month, count(*) AS new_outlets FROM sources GROUP BY ALL
), lasts AS (
    SELECT country, strftime(last_seen, '%Y-%m') AS month, count(*) AS last_seen_outlets FROM sources GROUP BY ALL
)
SELECT f.country, f.month, f.new_outlets, coalesce(l.last_seen_outlets, 0) AS last_seen_outlets
FROM firsts f
LEFT JOIN lasts l USING (country, month)
JOIN bounds b ON b.country = f.country
WHERE f.month > b.m0 AND f.month < b.m1
ORDER BY f.country, f.month;

-- which outlets appear in the same story cards: top 40 outlets per edition, strongest links
CREATE TABLE coappearance_nodes AS
SELECT country, outlet, appearances, leads, fair_lead_rate
FROM (SELECT *, row_number() OVER (PARTITION BY country ORDER BY appearances DESC, outlet) AS rk FROM sources)
WHERE rk <= 40;

CREATE TABLE coappearance_edges AS
WITH items AS (
    SELECT e.label AS country, i.story_id, i.outlet
    FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
    JOIN coappearance_nodes n ON n.country = e.label AND n.outlet = i.outlet
), pairs AS (
    SELECT a.country, a.outlet AS source, b.outlet AS target, count(DISTINCT a.story_id) AS together
    FROM items a JOIN items b ON a.story_id = b.story_id AND a.outlet < b.outlet
    GROUP BY ALL
)
SELECT p.*, round(p.together / sqrt(na.appearances * nb.appearances), 4) AS strength   -- cosine-style
FROM pairs p
JOIN coappearance_nodes na ON na.country = p.country AND na.outlet = p.source
JOIN coappearance_nodes nb ON nb.country = p.country AND nb.outlet = p.target
QUALIFY row_number() OVER (PARTITION BY p.country ORDER BY strength DESC) <= 120
ORDER BY p.country, strength DESC;

-- =====================================================================
-- Timing and freshness (lead articles)
-- =====================================================================

-- hour x weekday of publication, in the edition's local time
CREATE TABLE publication_hours AS
SELECT e.label AS country,
       dayofweek(timezone(e.tz, s.published_at::TIMESTAMPTZ)) AS weekday,   -- 0 = Sunday
       hour(timezone(e.tz, s.published_at::TIMESTAMPTZ))      AS hour,
       count(*) AS stories
FROM stories s JOIN editions e ON e.country = s.country
WHERE s.published_at IS NOT NULL
GROUP BY ALL ORDER BY country, weekday, hour;

-- how old the lead article is on the day of the feed snapshot
CREATE TABLE freshness AS
WITH a AS (
    SELECT e.label AS country, s.category,
           date_diff('day', timezone(e.tz, s.published_at::TIMESTAMPTZ)::DATE, s.file_date) AS age
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.published_at IS NOT NULL
)
SELECT country, category,
       CASE WHEN age <= 0 THEN 'same day' WHEN age = 1 THEN '1 day' WHEN age <= 3 THEN '2-3 days'
            WHEN age <= 7 THEN '4-7 days' ELSE 'older' END AS age_bucket,
       count(*) AS stories
FROM a GROUP BY ALL ORDER BY country, category, age_bucket;

-- section mix by weekday
CREATE TABLE weekday_mix AS
SELECT e.label AS country, dayofweek(s.file_date) AS weekday, s.category, count(*) AS stories
FROM stories s JOIN editions e ON e.country = s.country
GROUP BY ALL ORDER BY country, weekday, category;

-- =====================================================================
-- How the feed works
-- =====================================================================

CREATE TABLE cluster_size_monthly AS
SELECT e.label AS country, strftime(s.file_date, '%Y-%m') AS month,
       round(avg(s.cluster_size), 3)                  AS avg_cluster_size,
       round(avg((s.cluster_size = 1)::INT), 4)       AS single_share,
       count(*)                                       AS stories
FROM stories s JOIN editions e ON e.country = s.country
GROUP BY ALL ORDER BY country, month;

-- which wording Google used for its "full coverage" link, week by week (design changes)
CREATE TABLE link_phrase_weekly AS
SELECT e.label AS country, date_trunc('week', s.file_date)::DATE AS week,
       coalesce(nullif(s.link_phrase, ''), '(no link)') AS link_phrase, count(*) AS stories
FROM stories s JOIN editions e ON e.country = s.country
GROUP BY ALL ORDER BY country, week, link_phrase;

-- position in the daily file: do the top outlets get the first slots more than their share?
CREATE TABLE feed_position AS
WITH lead AS (
    SELECT e.label AS country, s.lead_outlet AS outlet, s.rank_in_file < 5 AS top5
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.lead_outlet <> ''
), tot AS (
    SELECT country, count(*) AS n, count(*) FILTER (WHERE top5) AS n_top5 FROM lead GROUP BY country
), per AS (
    SELECT country, outlet, count(*) AS leads, count(*) FILTER (WHERE top5) AS top5_leads FROM lead GROUP BY ALL
)
SELECT p.country, p.outlet, p.leads, p.top5_leads,
       round(p.leads / t.n, 4)       AS share_all,
       round(p.top5_leads / t.n_top5, 4) AS share_top5
FROM per p JOIN tot t USING (country)
QUALIFY row_number() OVER (PARTITION BY p.country ORDER BY p.leads DESC) <= 15
ORDER BY p.country, p.leads DESC;

-- =====================================================================
-- Headlines
-- =====================================================================

CREATE MACRO headline_features(h) AS STRUCT_PACK(
    chars    := length(h),
    words    := len(string_split(trim(h), ' ')),
    question := (h LIKE '%?%')::INT,
    exclaim  := (h LIKE '%!%')::INT,
    number   := regexp_matches(h, '[0-9]')::INT,
    quote    := regexp_matches(h, '["«»“”„]')::INT,
    colon    := (h LIKE '%:%')::INT
);

-- style of lead headlines per edition and per top outlet
CREATE TABLE headline_style AS
WITH h AS (
    SELECT e.label AS country, s.lead_outlet AS outlet, headline_features(s.title) AS f
    FROM stories s JOIN editions e ON e.country = s.country
    WHERE s.title IS NOT NULL AND s.title <> ''
), top AS (
    SELECT country, outlet FROM top_outlets
)
SELECT country, 'All outlets' AS outlet, count(*) AS headlines,
       round(avg(f.chars), 1) AS avg_chars, round(avg(f.words), 1) AS avg_words,
       round(avg(f.question), 4) AS question_share, round(avg(f.exclaim), 4) AS exclaim_share,
       round(avg(f.number), 4) AS number_share, round(avg(f.quote), 4) AS quote_share,
       round(avg(f.colon), 4) AS colon_share
FROM h GROUP BY country
UNION ALL
SELECT h.country, h.outlet, count(*),
       round(avg(f.chars), 1), round(avg(f.words), 1), round(avg(f.question), 4), round(avg(f.exclaim), 4),
       round(avg(f.number), 4), round(avg(f.quote), 4), round(avg(f.colon), 4)
FROM h JOIN top USING (country, outlet) GROUP BY h.country, h.outlet
ORDER BY country, headlines DESC;

-- lead vs related headlines inside the same story cards (2+ outlets)
CREATE TABLE lead_vs_related_headlines AS
WITH h AS (
    SELECT e.label AS country, CASE WHEN i.position = 0 THEN 'lead' ELSE 'related' END AS role,
           headline_features(i.headline) AS f
    FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
    WHERE s.cluster_size >= 2 AND i.headline IS NOT NULL AND i.headline <> ''
)
SELECT country, role, count(*) AS headlines,
       round(avg(f.chars), 1) AS avg_chars, round(avg(f.words), 1) AS avg_words,
       round(avg(f.question), 4) AS question_share, round(avg(f.exclaim), 4) AS exclaim_share,
       round(avg(f.number), 4) AS number_share, round(avg(f.quote), 4) AS quote_share,
       round(avg(f.colon), 4) AS colon_share
FROM h GROUP BY ALL ORDER BY country, role;

-- =====================================================================
-- Outlet profiles (for the search box): top 250 outlets per edition by appearances
-- =====================================================================

CREATE TABLE profile_outlets AS
SELECT country, outlet, website, appearances, leads, lead_rate, fair_lead_rate, first_seen, last_seen
FROM (SELECT *, row_number() OVER (PARTITION BY country ORDER BY appearances DESC, outlet) AS rk FROM sources)
WHERE rk <= 250;

CREATE TABLE profile_monthly AS
SELECT e.label AS country, i.outlet, strftime(s.file_date, '%Y-%m') AS month,
       count(*) AS appearances, count(*) FILTER (WHERE i.position = 0) AS leads
FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
JOIN profile_outlets p ON p.country = e.label AND p.outlet = i.outlet
GROUP BY ALL ORDER BY country, outlet, month;

CREATE TABLE profile_categories AS
SELECT b.country, b.outlet, b.category, b.appearances, b.leads
FROM sources_by_category b JOIN profile_outlets p USING (country, outlet)
ORDER BY country, outlet, appearances DESC;

CREATE TABLE profile_partners AS
WITH it AS (
    SELECT e.label AS country, i.story_id, i.outlet
    FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
    WHERE i.outlet <> '' AND s.cluster_size >= 2
), pairs AS (
    SELECT a.country, a.outlet, b.outlet AS partner, count(DISTINCT a.story_id) AS together
    FROM it a JOIN profile_outlets p ON p.country = a.country AND p.outlet = a.outlet
    JOIN it b ON a.story_id = b.story_id AND a.outlet <> b.outlet
    GROUP BY ALL
)
SELECT * FROM pairs
QUALIFY row_number() OVER (PARTITION BY country, outlet ORDER BY together DESC, partner) <= 8
ORDER BY country, outlet, together DESC;
