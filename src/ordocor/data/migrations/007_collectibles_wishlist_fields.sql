ALTER TABLE investment_collectibles ADD COLUMN target_price REAL NOT NULL DEFAULT 0;
ALTER TABLE investment_collectibles ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1;
