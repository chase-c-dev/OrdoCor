from __future__ import annotations

import math
from datetime import date

import pytest

from ordocor.services.market_data import (
    HistoricalPrice,
    MarketDataError,
    MarketDataWorker,
    MarketHistoryWorker,
    MarketQuote,
    YahooFinanceProvider,
)


class FakeTicker:
    def __init__(self, info=None, fast_price=0, info_error: Exception | None = None):
        self._info = info or {}
        self._info_error = info_error
        self.fast_info = {"last_price": fast_price}

    def get_info(self):
        if self._info_error:
            raise self._info_error
        return self._info


class FakeHistory:
    def __init__(self, rows):
        self.rows = rows

    def iterrows(self):
        return iter(self.rows)


def test_provider_uses_quote_information(monkeypatch):
    ticker = FakeTicker({"currentPrice": 12.5, "dividendRate": 0.5})
    monkeypatch.setattr("yfinance.Ticker", lambda symbol: ticker)
    provider = YahooFinanceProvider()

    quote = provider.fetch_quote(" f ")

    assert quote.ticker == "F"
    assert quote.market_price == 12.5
    assert quote.dividend_yield == 4
    assert quote.fetched_at.endswith("+00:00")


def test_provider_falls_back_to_fast_price_and_rejects_invalid_quotes():
    fallback = YahooFinanceProvider(
        lambda symbol: FakeTicker(info_error=RuntimeError("offline"), fast_price=9.75)
    )
    assert fallback.fetch_quote("ex").market_price == 9.75
    assert fallback.fetch_quote("ex").dividend_yield is None

    reported_yield = YahooFinanceProvider(
        lambda symbol: FakeTicker({"regularMarketPrice": 10, "dividendYield": 3.2})
    )
    assert reported_yield.fetch_quote("div").dividend_yield == 3.2

    mutual_fund = YahooFinanceProvider(
        lambda symbol: FakeTicker(
            {
                "quoteType": "MUTUALFUND",
                "regularMarketPrice": 500,
                "yield": 0.012,
                "dividendRate": 1,
            }
        )
    )
    assert mutual_fund.fetch_quote("fund").dividend_yield == 1.2

    invalid = FakeTicker({"regularMarketPrice": math.nan})
    invalid.fast_info = {}
    provider = YahooFinanceProvider(lambda symbol: invalid)
    with pytest.raises(MarketDataError, match="No current market price"):
        provider.fetch_quote("bad")

    assert provider._number("not a number") is None


def test_market_data_worker_reports_quotes_and_errors():
    quote = MarketQuote("GOOD", 20, 2.5, "2026-06-21T12:00:00+00:00")

    class Provider:
        def fetch_quote(self, ticker):
            if ticker == "BAD":
                raise MarketDataError("Unavailable")
            return quote

    completed = []
    worker = MarketDataWorker(("GOOD", "BAD"), Provider())
    worker.signals.completed.connect(lambda quotes, errors: completed.append((quotes, errors)))

    worker.run()

    assert completed == [({"GOOD": quote}, {"BAD": "Market data unavailable."})]


def test_provider_and_worker_price_history(monkeypatch):
    class HistoryTicker:
        def history(self, **kwargs):
            return FakeHistory(
                (
                    (type("Index", (), {"date": lambda self: date(2026, 1, 2)})(), {"Close": 10}),
                    (type("Index", (), {"date": lambda self: date(2026, 1, 3)})(), {"Close": None}),
                )
            )

    monkeypatch.setattr("yfinance.Ticker", lambda symbol: HistoryTicker())
    provider = YahooFinanceProvider()
    prices = provider.fetch_history(" fund ")
    assert prices == (HistoricalPrice("2026-01-02", 10),)

    empty_provider = YahooFinanceProvider(
        lambda symbol: type(
            "EmptyTicker",
            (),
            {"history": lambda self, **kwargs: FakeHistory(())},
        )()
    )
    with pytest.raises(MarketDataError, match="No price history"):
        empty_provider.fetch_history("EMPTY")

    completed = []
    failed = []
    worker = MarketHistoryWorker("FUND", provider)
    worker.signals.completed.connect(completed.append)
    worker.run()
    assert completed == [prices]

    worker = MarketHistoryWorker("EMPTY", empty_provider)
    worker.signals.failed.connect(failed.append)
    worker.run()
    assert failed == ["Market data unavailable."]
