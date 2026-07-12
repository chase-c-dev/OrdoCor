ALTER TABLE investment_stocks ADD COLUMN purchase_date TEXT;
ALTER TABLE investment_stocks ADD COLUMN purchase_price REAL NOT NULL DEFAULT 0;
ALTER TABLE investment_stocks ADD COLUMN target_sell_price REAL NOT NULL DEFAULT 0;
