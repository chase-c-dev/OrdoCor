# Investing Module

## Scope

The Investing section is organized around:

- Accounts
- Stocks
- Mutual funds
- Banking products, including certificates of deposit
- Collectibles Wishlist
- Investment Plans

## Core Entities

### Accounts

Accounts represent financial accounts grouped by institution.

Suggested fields:

- `institution`
- `name`
- `account_type`

Supported account types:

- Brokerage
- Savings
- Checking
- Credit

### Stocks

Stocks represent individual company positions.

Suggested fields:

- `ticker`
- `company_name`
- `purchase_date`
- `purchase_price`
- `shares`
- `target_sell_price`

Calculated display values:

- Cost basis: purchase price x shares
- Market value: latest market price x shares
- Dollar gain/loss: market value - cost basis
- Percentage return: (market price - purchase price) / purchase price
- Dividend yield reported by the market-data provider

### Stock Market Data

Entering the Stocks tab automatically refreshes the latest available market price and dividend
yield for each distinct ticker through `yfinance`. A **Refresh Market Data** action is also
available. Requests run outside the GUI thread. Market data can be delayed by exchanges or the
upstream provider and should not be treated as execution-grade pricing.

Successful quotes are cached in `investment_stocks` with their retrieval timestamp. Cached values
remain visible when OrdoCor is offline. If one ticker fails, its previous cached value is preserved
while other tickers continue updating.

Only stock ticker and mutual fund symbols are sent to the provider. Purchase dates, purchase
prices, share counts, target prices, calculated gains, and other personal records are never
included in market-data requests.

### Security Details and Price History

Double-clicking a stock or mutual fund opens its detail window. Modify and Remove actions are kept
inside this window instead of the main tables. Removal requires confirmation.

Each detail window includes locally stored notes and an interactive closing-price chart. Notes save
automatically when the detail window closes. Opening the window automatically refreshes up to five
years of daily history. The chart supports `1D`, `5D`, `1M`, `6M`, `1Y`, `3Y`, and `5Y` range
filters, and hovering over the line shows the date and closing price. Successful history is cached
in SQLite so it remains available offline; a failed refresh leaves the previous chart untouched.

### Mutual Funds

Mutual funds represent pooled investment funds held directly or through an account.

Suggested fields:

- `symbol`
- `fund_name`
- `purchase_date`
- `purchase_price`
- `shares`

Calculated display values:

- Cost basis: purchase price x shares
- Market value: latest market price x shares
- Dollar gain/loss: market value - cost basis
- Percentage return: (market price - purchase price) / purchase price
- Dividend yield when reported by the market-data provider

Entering the Mutual Funds tab automatically refreshes its symbols. The page also has a **Refresh
Market Data** action and uses the same background quote service and offline cache as Stocks.
Successful fund quotes are stored in `investment_mutual_funds`; a failed refresh preserves the last
successful values.

### Banking

Banking currently tracks certificates of deposit.

Suggested fields:

- `institution`
- `product_name`
- `open_date`
- `principal`
- `interest_rate`
- `maturity_date`
- `maturity_value`

### Collectibles Wishlist

The collectibles wishlist tracks desired collectible purchases before they are acquired.

Suggested fields:

- `item_name`
- `category`
- `target_price`
- `quantity`

### Investment Plans

Investment plans track future stock and mutual fund purchases before money is committed.

Suggested fields:

- `idea_name`
- `investment_type`
- `desired_purchase_price`
- `desired_shares`
- `notes`

The notes field stores formatted HTML from the rich-text notes editor.

## Later Enhancements

- Dividend payment tracking for stocks and funds
- Allocation targets
- Import from CSV exports
- Tax lots for marketable securities
- Retirement projections
