ALTER TABLE investment_pipeline ADD COLUMN investment_type TEXT NOT NULL DEFAULT 'Stock';
ALTER TABLE investment_pipeline ADD COLUMN desired_purchase_price REAL NOT NULL DEFAULT 0;
ALTER TABLE investment_pipeline ADD COLUMN desired_shares REAL NOT NULL DEFAULT 0;
