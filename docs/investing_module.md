# Investing Module

## Scope

The Investing section is organized around:

- Accounts
- Stocks for open positions or owned stocks
- Stock Watchlist
- Mutual funds for open positions or owned mutual funds
- Mutual Fund Watchlist
- Banking products, including certificates of deposit
- Collectibles
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

Stocks represent open positions or owned individual company positions.

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
yield for each distinct ticker through Yahoo Finance. A **Refresh Market Data** action is also
available. Requests run asynchronously in the Electron main process. Market data can be delayed by
exchanges or the upstream provider and should not be treated as execution-grade pricing.

Successful quotes are cached in `investment_stocks` with their retrieval timestamp. Cached values
remain visible when OrdoCor is offline. If one ticker fails, its previous cached value is preserved
while other tickers continue updating.

Only stock ticker and mutual fund symbols are sent to the provider. Purchase dates, purchase
prices, share counts, target prices, calculated gains, and other personal records are never
included in market-data requests.

### Security Details and Price History

Selecting a stock, mutual fund, stock watchlist item, or mutual fund watchlist item opens its
detail view. Edit and Remove actions are kept inside this view instead of the main stock and
mutual fund tables. Removal requires confirmation.

Each detail window includes locally stored notes and an interactive closing-price chart. Notes save
automatically when the detail window closes. Opening the window automatically refreshes up to five
years of daily history. The chart supports `1D`, `5D`, `1M`, `6M`, `1Y`, `3Y`, and `5Y` range
filters, and hovering over the line shows the date and closing price. Successful history is cached
in SQLite so it remains available offline; a failed refresh leaves the previous chart untouched.

The detail window also includes a collapsible **More Info** section. It refreshes live reference
data when online, such as market cap, P/E, EPS, beta, exchange, sector, industry, 52-week range,
average volume, total assets, expense ratio, and fund category when those values are available
from the provider. This area is horizontally arranged so it can show several fields per row and
stay compact on smaller monitors.

An **Analyst Recommendations** section shows the provider's available consensus, recommendation
score, analyst count, price targets, and strong-buy/buy/hold/sell/strong-sell trend totals. Recent
firm ratings are included as reported, including Overweight and Underweight ratings when available.
Recommendations are informational, may be delayed or unavailable, and are not financial advice.

### Mutual Funds

Mutual funds represent open positions or owned pooled investment funds held directly or through an
account.

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

### Watchlists

Stock Watchlist and Mutual Fund Watchlist track securities the user may want to buy later.

Suggested fields:

- `symbol` or `ticker`
- `name`
- `target_buy_price`

Calculated display values:

- Latest market price
- Dollar difference from the target buy price
- Percentage difference from the target buy price
- Dividend yield when reported by the market-data provider

Rows are highlighted when the live or cached market price is at or below the target buy price, so
ready-to-buy items stand out. Entering either watchlist tab refreshes market data in the
background. Double-clicking a watchlist item opens the same chart, notes, and **More Info** detail
window used by owned stocks and mutual funds.

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

### Collectibles

Collectibles track desired collectible purchases before they are acquired.

Suggested fields:

- `item_name`
- `category`
- `target_price`
- `quantity`

Double-clicking a collectible opens a detail window for notes and a purchase link. Notes and the
purchase link save automatically when the window closes.

### Investment Plans

Investment plans track future stock and mutual fund purchases before money is committed.

Suggested fields:

- `idea_name`
- `investment_type`
- `desired_purchase_price`
- `desired_shares`
- `notes`

The notes field stores detailed plain text entered in the plan editor.

## Later Enhancements

- Dividend payment tracking for stocks and funds
- Allocation targets
- Import from CSV exports
- Tax lots for marketable securities
- Retirement projections
