-- Raw tables, loaded from the build_tables.py outputs on carrot.

CREATE TABLE IF NOT EXISTS editions (
    country text PRIMARY KEY,          -- folder name: US, FR, Germany, Romania
    label   text NOT NULL,             -- shown on the site
    sort    int  NOT NULL
);
INSERT INTO editions VALUES ('US', 'United States', 1), ('FR', 'France', 2),
                            ('Germany', 'Germany', 3), ('Romania', 'Romania', 4)
ON CONFLICT (country) DO NOTHING;

-- one row per story card (the lead article)
CREATE TABLE IF NOT EXISTS stories (
    story_id      text PRIMARY KEY,    -- country|category|date|rank
    country       text NOT NULL REFERENCES editions,
    category      text NOT NULL,       -- Business, Health, Nation, Politics, Science, Technology, World
    file_date     date NOT NULL,
    rank_in_file  int,                 -- row order in the daily file (possibly feed order)
    title         text,
    lead_outlet   text,
    lead_website  text,
    published_at  timestamp,
    url           text,
    cluster_size  int                  -- number of articles in the card (1 = lead only)
);
CREATE INDEX IF NOT EXISTS stories_country_cat_date ON stories (country, category, file_date);

-- one row per article in a story card; position 0 = lead
CREATE TABLE IF NOT EXISTS cluster_items (
    story_id  text NOT NULL REFERENCES stories ON DELETE CASCADE,
    position  int  NOT NULL,
    headline  text,
    outlet    text,
    parse     text,                    -- known | heuristic | failed
    PRIMARY KEY (story_id, position)
);
CREATE INDEX IF NOT EXISTS cluster_items_outlet ON cluster_items (outlet);

-- stories per daily file, including empty files (to see collection gaps)
CREATE TABLE IF NOT EXISTS coverage (
    country   text NOT NULL REFERENCES editions,
    category  text NOT NULL,
    date      date NOT NULL,
    n_stories int  NOT NULL,
    PRIMARY KEY (country, category, date)
);
