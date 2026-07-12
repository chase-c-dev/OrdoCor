from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from PySide6.QtCore import QObject, QRunnable, Signal


class MarketDataError(Exception):
    """Raised when a usable market quote cannot be retrieved."""


@dataclass(frozen=True)
class MarketQuote:
    ticker: str
    market_price: float
    dividend_yield: float | None
    fetched_at: str


@dataclass(frozen=True)
class HistoricalPrice:
    price_date: str
    close_price: float


class YahooFinanceProvider:
    def __init__(self, ticker_factory: Callable[[str], object] | None = None) -> None:
        self.ticker_factory = ticker_factory

    def fetch_quote(self, ticker_symbol: str) -> MarketQuote:
        symbol = ticker_symbol.strip().upper()
        ticker_factory = self.ticker_factory
        if ticker_factory is None:
            import yfinance

            ticker_factory = yfinance.Ticker
        ticker = ticker_factory(symbol)
        try:
            info = ticker.get_info()
        except Exception:
            info = {}

        price = self._number(info.get("currentPrice") or info.get("regularMarketPrice"))
        if price is None:
            try:
                price = self._number(ticker.fast_info["last_price"])
            except Exception:
                price = None
        if price is None or price <= 0:
            raise MarketDataError(f"No current market price was available for {symbol}.")

        fund_yield = self._number(info.get("yield"))
        dividend_rate = self._number(info.get("dividendRate"))
        if str(info.get("quoteType", "")).upper() == "MUTUALFUND" and fund_yield is not None:
            dividend_yield = fund_yield * 100
        elif dividend_rate is not None:
            dividend_yield = (dividend_rate / price) * 100
        else:
            dividend_yield = self._number(info.get("dividendYield"))
        return MarketQuote(
            ticker=symbol,
            market_price=price,
            dividend_yield=dividend_yield,
            fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    def fetch_history(self, ticker_symbol: str) -> tuple[HistoricalPrice, ...]:
        symbol = ticker_symbol.strip().upper()
        ticker_factory = self.ticker_factory
        if ticker_factory is None:
            import yfinance

            ticker_factory = yfinance.Ticker
        history = ticker_factory(symbol).history(period="5y", interval="1d", auto_adjust=False)
        prices = tuple(
            HistoricalPrice(index.date().isoformat(), close_price)
            for index, row in history.iterrows()
            if (close_price := self._number(row.get("Close"))) is not None
        )
        if not prices:
            raise MarketDataError(f"No price history was available for {symbol}.")
        return prices

    @staticmethod
    def _number(value: object) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None


class MarketDataSignals(QObject):
    completed = Signal(object, object)


class MarketDataWorker(QRunnable):
    def __init__(
        self,
        tickers: Iterable[str],
        provider: YahooFinanceProvider | None = None,
    ) -> None:
        super().__init__()
        self.tickers = tuple(tickers)
        self.provider = provider or YahooFinanceProvider()
        self.signals = MarketDataSignals()

    def run(self) -> None:
        quotes: dict[str, MarketQuote] = {}
        errors: dict[str, str] = {}
        for ticker in self.tickers:
            try:
                quotes[ticker] = self.provider.fetch_quote(ticker)
            except Exception:
                errors[ticker] = "Market data unavailable."
        self.signals.completed.emit(quotes, errors)


class MarketHistorySignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class MarketHistoryWorker(QRunnable):
    def __init__(
        self,
        ticker: str,
        provider: YahooFinanceProvider | None = None,
    ) -> None:
        super().__init__()
        self.ticker = ticker
        self.provider = provider or YahooFinanceProvider()
        self.signals = MarketHistorySignals()

    def run(self) -> None:
        try:
            prices = self.provider.fetch_history(self.ticker)
        except Exception:
            self.signals.failed.emit("Market data unavailable.")
            return
        self.signals.completed.emit(prices)
