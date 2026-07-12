CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    servings INTEGER NOT NULL DEFAULT 0,
    prep_minutes INTEGER NOT NULL DEFAULT 0,
    cook_minutes INTEGER NOT NULL DEFAULT 0,
    ingredients TEXT,
    instructions TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recipes_category_name
ON recipes (category, name);
