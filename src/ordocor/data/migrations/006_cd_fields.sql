ALTER TABLE investment_banking_products ADD COLUMN open_date TEXT;
ALTER TABLE investment_banking_products ADD COLUMN maturity_value REAL NOT NULL DEFAULT 0;
