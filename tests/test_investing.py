from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QMessageBox

from ordocor.ui.pages.investing import InvestingPage
from ordocor.ui.pages.investing import (
    accounts,
    banking,
    collectibles,
    mutual_funds,
    plans,
    stocks,
)
from ordocor.services.market_data import MarketQuote


CASES = [
    (
        accounts,
        "AccountDialog",
        "account_data",
        {"institution": "Bank", "name": "Checking", "account_type": "checking"},
        "_add_account",
        "_modify_account",
        "_remove_account",
        "accounts_table",
        "_validate_account",
        "investment_accounts",
    ),
    (
        stocks,
        "StockDialog",
        "stock_data",
        {
            "stock_name": "Example",
            "ticker": "EX",
            "purchase_date": "2026-01-01",
            "purchase_price": 10,
            "shares": 2,
            "target_sell_price": 15,
        },
        "_add_stock",
        "_modify_stock",
        "_remove_stock",
        "stocks_table",
        "_validate_stock",
        "investment_stocks",
    ),
    (
        mutual_funds,
        "MutualFundDialog",
        "fund_data",
        {
            "fund_name": "Index",
            "symbol": "IDX",
            "purchase_date": "2026-01-01",
            "purchase_price": 20,
            "shares": 3,
        },
        "_add_mutual_fund",
        "_modify_mutual_fund",
        "_remove_mutual_fund",
        "mutual_funds_table",
        "_validate_mutual_fund",
        "investment_mutual_funds",
    ),
    (
        banking,
        "CertificateOfDepositDialog",
        "cd_data",
        {
            "product_name": "CD",
            "institution": "Bank",
            "open_date": "2026-01-01",
            "principal": 1000,
            "interest_rate": 4,
            "maturity_date": "2027-01-01",
            "maturity_value": 1040,
        },
        "_add_cd",
        "_modify_cd",
        "_remove_cd",
        "banking_table",
        "_validate_cd",
        "investment_banking_products",
    ),
    (
        collectibles,
        "CollectibleDialog",
        "collectible_data",
        {"item_name": "Coin", "category": "Coin", "target_price": 50, "quantity": 2},
        "_add_collectible",
        "_modify_collectible",
        "_remove_collectible",
        "collectibles_table",
        "_validate_collectible",
        "investment_collectibles",
    ),
    (
        plans,
        "InvestmentPlanDialog",
        "plan_data",
        {
            "idea_name": "Index",
            "investment_type": "Stock",
            "desired_purchase_price": 25,
            "desired_shares": 4,
            "notes": "<p>Research</p>",
        },
        "_add_investment_plan",
        "_modify_investment_plan",
        "_remove_investment_plan",
        "investment_plans_table",
        "_validate_investment_plan",
        "investment_pipeline",
    ),
]


def fake_dialog(data_method: str, data: dict[str, object], result=QDialog.Accepted):
    return SimpleNamespace(exec=lambda: result, **{data_method: lambda: data})


@pytest.mark.parametrize(
    (
        "module",
        "dialog_name",
        "data_method",
        "data",
        "add_method",
        "modify_method",
        "remove_method",
        "table_name",
        "validate_method",
        "database_table",
    ),
    CASES,
)
def test_investing_crud_workflows(
    qapp,
    database,
    monkeypatch,
    module,
    dialog_name,
    data_method,
    data,
    add_method,
    modify_method,
    remove_method,
    table_name,
    validate_method,
    database_table,
):
    page = InvestingPage(database)
    table = getattr(page, table_name)
    monkeypatch.setattr(module, dialog_name, lambda *args: fake_dialog(data_method, data))

    getattr(page, add_method)()
    assert table.rowCount() == 1

    table.selectRow(0)
    getattr(page, modify_method)()
    assert table.rowCount() == 1

    rejected = fake_dialog(data_method, data, QDialog.Rejected)
    monkeypatch.setattr(module, dialog_name, lambda *args: rejected)
    table.selectRow(0)
    getattr(page, modify_method)()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    invalid = dict(data)
    first_required = next(key for key, value in invalid.items() if isinstance(value, str))
    invalid[first_required] = ""
    monkeypatch.setattr(
        module,
        dialog_name,
        lambda *args: fake_dialog(data_method, invalid),
    )
    table.selectRow(0)
    getattr(page, modify_method)()

    with database.connect() as connection:
        connection.execute(f"DELETE FROM {database_table}")
    table.selectRow(0)
    getattr(page, modify_method)()

    table.selectRow(0)
    getattr(page, remove_method)()
    assert table.rowCount() == 0

    getattr(page, modify_method)()
    getattr(page, remove_method)()

    monkeypatch.setattr(
        module,
        dialog_name,
        lambda *args: fake_dialog(data_method, data, QDialog.Rejected),
    )
    getattr(page, add_method)()
    assert table.rowCount() == 0

    monkeypatch.setattr(
        module,
        dialog_name,
        lambda *args: fake_dialog(data_method, invalid),
    )
    getattr(page, add_method)()
    assert getattr(page, validate_method)(invalid) is False


def test_investing_formatters(database):
    page = InvestingPage(database)
    assert page._money(None) == "$0.00"
    assert page._money(1234.5) == "$1,234.50"
    assert page._number(1.25) == "1.25"
    assert page._percent(4.25) == "4.25%"
    assert page._optional_money(None) == "-"
    assert page._optional_money(12.5, signed=True) == "+$12.50"
    assert page._optional_money(-2, signed=True) == "-$2.00"
    assert page._optional_money(2) == "$2.00"
    assert page._optional_percent(None) == "-"
    assert page._optional_percent(4.5, signed=True) == "+4.5%"


def test_investing_market_tables_fit_headers_without_horizontal_scroll(database):
    page = InvestingPage(database)
    compact_market_tables = (
        page.stocks_table,
        page.mutual_funds_table,
    )
    for table in compact_market_tables:
        assert table.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
        assert table.horizontalHeader().sectionResizeMode(0) == QHeaderView.Stretch
        assert table.horizontalHeader().height() >= 44
        assert table.horizontalHeader().minimumSectionSize() <= 48

    assert page.stocks_table.horizontalHeaderItem(11).text() == "Dividend\nYield"
    assert page.mutual_funds_table.horizontalHeaderItem(10).text() == "Dividend\nYield"

    standard_tables = (
        page.accounts_table,
        page.banking_table,
        page.collectibles_table,
        page.investment_plans_table,
    )
    for table in standard_tables:
        assert table.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
        assert table.horizontalHeader().sectionResizeMode(0) == QHeaderView.Stretch


def test_stock_market_values_and_refresh_workflow(database, monkeypatch):
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO investment_stocks (
                ticker, company_name, purchase_date, purchase_price, shares, target_sell_price,
                market_price, dividend_yield, market_updated_at
            )
            VALUES ('F', 'Ford', '2026-01-01', 10, 5, 15, 12, 4.5, 'cached')
            """
        )
        connection.execute(
            """
            INSERT INTO investment_stocks (
                ticker, company_name, purchase_date, purchase_price, shares, target_sell_price,
                market_price, dividend_yield, market_updated_at
            )
            VALUES ('Z', 'Zenith', '2026-01-01', 10, 5, 15, 8, 0, 'cached')
            """
        )

    page = InvestingPage(database)
    assert page.stocks_table.item(0, 5).text() == "$50.00"
    assert page.stocks_table.item(0, 7).text() == "$12.00"
    assert page.stocks_table.item(0, 8).text() == "$60.00"
    assert page.stocks_table.item(0, 9).text() == "+$10.00"
    assert page.stocks_table.item(0, 10).text() == "+20%"
    assert page.stocks_table.item(0, 11).text() == "4.5%"
    assert page.stocks_table.item(0, 9).foreground().color().name().lower() == "#66d98f"
    assert page.stocks_table.item(0, 10).foreground().color().name().lower() == "#66d98f"
    assert page.stocks_table.item(1, 9).text() == "-$10.00"
    assert page.stocks_table.item(1, 9).foreground().color().name().lower() == "#ff6b6b"
    assert page.stocks_table.item(0, 7).toolTip() == "Updated: cached"

    started = []
    page._market_thread_pool = SimpleNamespace(start=lambda worker: started.append(worker))
    monkeypatch.setattr(
        stocks,
        "MarketDataWorker",
        lambda tickers: SimpleNamespace(
            tickers=tickers,
            signals=SimpleNamespace(completed=SimpleNamespace(connect=lambda callback: None)),
        ),
    )
    page._refresh_market_data()
    assert started[0].tickers == ("F", "Z")
    assert not page.market_refresh_button.isEnabled()
    page._refresh_market_data()
    assert len(started) == 1

    quote = MarketQuote("F", 14, 0, "2026-06-21T12:00:00+00:00")
    page._market_data_refreshed({"F": quote}, {})
    assert page.stocks_table.item(0, 8).text() == "$70.00"
    assert page.market_status.text() == "Updated market data for 1 ticker(s)."
    assert page.market_refresh_button.isEnabled()
    assert page._market_worker is None

    page._market_data_refreshed({"F": quote}, {"BAD": "Unavailable"})
    assert "1 could not be refreshed" in page.market_status.text()
    page._market_data_refreshed({}, {"F": "Offline"})
    assert page.market_status.text().startswith("Market data is unavailable")


def test_stock_refresh_without_holdings(database):
    page = InvestingPage(database)
    page._refresh_market_data()
    assert page.market_status.text() == "Add a stock before refreshing market data."


def test_mutual_fund_market_values_and_refresh_workflow(database, monkeypatch):
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO investment_mutual_funds (
                symbol, fund_name, purchase_date, purchase_price, shares,
                market_price, dividend_yield, market_updated_at
            )
            VALUES ('VFIAX', 'Vanguard 500 Index', '2026-01-01', 500, 2, 550, 1.2, 'cached')
            """
        )
        connection.execute(
            """
            INSERT INTO investment_mutual_funds (
                symbol, fund_name, purchase_date, purchase_price, shares,
                market_price, dividend_yield, market_updated_at
            )
            VALUES ('ZIDX', 'Zenith Index', '2026-01-01', 100, 2, 90, 0, 'cached')
            """
        )

    page = InvestingPage(database)
    assert page.mutual_funds_table.item(0, 5).text() == "$1,000.00"
    assert page.mutual_funds_table.item(0, 6).text() == "$550.00"
    assert page.mutual_funds_table.item(0, 7).text() == "$1,100.00"
    assert page.mutual_funds_table.item(0, 8).text() == "+$100.00"
    assert page.mutual_funds_table.item(0, 9).text() == "+10%"
    assert page.mutual_funds_table.item(0, 10).text() == "1.2%"
    assert page.mutual_funds_table.item(0, 8).foreground().color().name().lower() == "#66d98f"
    assert page.mutual_funds_table.item(0, 9).foreground().color().name().lower() == "#66d98f"
    assert page.mutual_funds_table.item(1, 8).text() == "-$20.00"
    assert page.mutual_funds_table.item(1, 8).foreground().color().name().lower() == "#ff6b6b"
    assert page.mutual_funds_table.item(0, 6).toolTip() == "Updated: cached"

    started = []
    page._mutual_fund_thread_pool = SimpleNamespace(start=lambda worker: started.append(worker))
    monkeypatch.setattr(
        mutual_funds,
        "MarketDataWorker",
        lambda symbols: SimpleNamespace(
            tickers=symbols,
            signals=SimpleNamespace(completed=SimpleNamespace(connect=lambda callback: None)),
        ),
    )
    page._refresh_mutual_fund_market_data()
    assert started[0].tickers == ("VFIAX", "ZIDX")
    assert not page.mutual_fund_refresh_button.isEnabled()
    page._refresh_mutual_fund_market_data()
    assert len(started) == 1

    quote = MarketQuote("VFIAX", 575, 1.3, "2026-06-21T12:00:00+00:00")
    page._mutual_fund_market_data_refreshed({"VFIAX": quote}, {})
    assert page.mutual_funds_table.item(0, 7).text() == "$1,150.00"
    assert page.mutual_fund_market_status.text() == "Updated market data for 1 fund(s)."
    assert page.mutual_fund_refresh_button.isEnabled()
    assert page._mutual_fund_market_worker is None

    page._mutual_fund_market_data_refreshed({"VFIAX": quote}, {"BAD": "Unavailable"})
    assert "1 could not be refreshed" in page.mutual_fund_market_status.text()
    page._mutual_fund_market_data_refreshed({}, {"VFIAX": "Offline"})
    assert page.mutual_fund_market_status.text().startswith("Market data is unavailable")

    neutral_item = page.mutual_funds_table.item(0, 8)
    page._apply_mutual_fund_performance_color(neutral_item, None)
    page._apply_mutual_fund_performance_color(neutral_item, 0)
    page._apply_mutual_fund_performance_color(neutral_item, 1)


def test_mutual_fund_refresh_without_holdings(database):
    page = InvestingPage(database)
    page._refresh_mutual_fund_market_data()
    assert (
        page.mutual_fund_market_status.text() == "Add a mutual fund before refreshing market data."
    )


def test_entering_market_tabs_refreshes_data(database, monkeypatch):
    page = InvestingPage(database)
    refreshed = []
    monkeypatch.setattr(page, "_refresh_market_data", lambda: refreshed.append("stock"))
    monkeypatch.setattr(
        page,
        "_refresh_mutual_fund_market_data",
        lambda: refreshed.append("fund"),
    )
    page._refresh_active_market_data(0)
    page._refresh_active_market_data(1)
    page._refresh_active_market_data(2)
    assert refreshed == ["stock", "fund"]
