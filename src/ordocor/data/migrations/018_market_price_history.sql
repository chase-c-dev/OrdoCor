CREATE TABLE IF NOT EXISTS market_price_history (
    symbol TEXT NOT NULL,
    price_date TEXT NOT NULL,
    close_price REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, price_date)
);

CREATE INDEX IF NOT EXISTS idx_market_price_history_symbol_date
ON market_price_history (symbol, price_date);
