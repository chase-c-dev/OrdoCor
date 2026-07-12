CREATE TABLE IF NOT EXISTS travel_destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT,
    city TEXT,
    priority TEXT NOT NULL DEFAULT 'Medium',
    target_season TEXT,
    target_year INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_travel_destinations_country_city
ON travel_destinations (country, city);
