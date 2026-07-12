ALTER TABLE investment_mutual_funds ADD COLUMN purchase_date TEXT;
ALTER TABLE investment_mutual_funds ADD COLUMN purchase_price REAL NOT NULL DEFAULT 0;
