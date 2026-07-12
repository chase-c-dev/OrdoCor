from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QDateTime, QPointF, Qt
from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton, QTableWidgetItem

from ordocor.services.market_data import HistoricalPrice
from ordocor.ui.pages.investing import InvestingPage, mutual_funds, stocks
from ordocor.ui.pages.investing import details as details_module
from ordocor.ui.pages.investing.details import PriceHistoryChart, SecurityDetailDialog


def test_price_history_chart_filters_and_hover(qapp):
    chart = PriceHistoryChart()
    chart.set_prices(())
    chart.set_range("invalid")
    prices = (
        HistoricalPrice("2025-06-20", 90),
        HistoricalPrice("2026-05-25", 100),
        HistoricalPrice("2026-06-10", 110),
        HistoricalPrice("2026-06-14", 80),
        HistoricalPrice("2026-06-15", 85),
        HistoricalPrice("2026-06-20", 105),
    )
    chart.set_prices(prices)
    assert chart.series.count() == 6
    chart.set_range("5D")
    assert chart.series.count() == 2
    chart.set_range("1D")
    assert chart.series.count() == 1
    chart.set_range("1M")
    assert chart.series.count() == 5

    timestamp = QDateTime.fromString("2026-06-20T00:00:00+00:00", Qt.ISODate).toMSecsSinceEpoch()
    chart._show_hover(QPointF(timestamp, 105), True)
    assert "Jun 20, 2026" in chart.hover_label.text()
    chart._show_hover(QPointF(), False)
    assert chart.hover_label.text().startswith("Hover over")


def test_security_detail_notes_cache_and_history_refresh(qapp, database, monkeypatch):
    with database.connect() as connection:
        stock_id = connection.execute(
            "INSERT INTO investment_stocks (ticker, company_name, notes) VALUES ('F', 'Ford', '')"
        ).lastrowid
        fund_id = connection.execute(
            """
            INSERT INTO investment_mutual_funds (symbol, fund_name, notes)
            VALUES ('VFIAX', 'Vanguard', '')
            """
        ).lastrowid
        connection.execute(
            """
            INSERT INTO market_price_history (symbol, price_date, close_price)
            VALUES ('F', '2026-01-01', 10)
            """
        )

    scheduled = []
    monkeypatch.setattr(
        details_module.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append(callback),
    )
    dialog = SecurityDetailDialog(database, "stock", stock_id, "Ford", "F", "Initial")
    assert scheduled == [dialog._refresh_history]
    assert dialog.history_chart.series.count() == 1
    assert "Save Notes" not in [button.text() for button in dialog.findChildren(QPushButton)]
    dialog.notes_input.setPlainText("Long-term notes")
    dialog.done(QDialog.Accepted)
    assert dialog.notes_status.text() == "Notes saved."
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT notes FROM investment_stocks WHERE id = ?", (stock_id,)
            ).fetchone()[0]
            == "Long-term notes"
        )

    started = []
    fake_worker = SimpleNamespace(
        signals=SimpleNamespace(
            completed=SimpleNamespace(connect=lambda callback: None),
            failed=SimpleNamespace(connect=lambda callback: None),
        )
    )
    monkeypatch.setattr(details_module, "MarketHistoryWorker", lambda symbol: fake_worker)
    dialog._thread_pool = SimpleNamespace(start=lambda worker: started.append(worker))
    dialog._refresh_history()
    assert started == [fake_worker]
    assert not dialog.refresh_chart_button.isEnabled()
    dialog._refresh_history()
    assert started == [fake_worker]

    prices = (
        HistoricalPrice("2026-01-02", 11),
        HistoricalPrice("2026-01-03", 12),
    )
    dialog._history_refreshed(prices)
    assert dialog.history_status.text() == "Five-year price history updated."
    assert dialog.refresh_chart_button.isEnabled()
    assert dialog._history_worker is None

    dialog._history_failed("Market data unavailable.")
    assert dialog.history_status.text() == "Could not refresh chart: Market data unavailable."

    fund_dialog = SecurityDetailDialog(
        database, "mutual_fund", fund_id, "Vanguard", "VFIAX", "", auto_refresh=False
    )
    assert fund_dialog.history_status.text().startswith("No cached history")
    fund_dialog.notes_input.setPlainText("Fund notes")
    fund_dialog.done(QDialog.Rejected)
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT notes FROM investment_mutual_funds WHERE id = ?", (fund_id,)
            ).fetchone()[0]
            == "Fund notes"
        )


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class FakeDetailDialog:
    instances = []

    def __init__(self, *args):
        self.args = args
        self.modify_requested = FakeSignal()
        self.remove_requested = FakeSignal()
        self.accepted = 0
        self.instances.append(self)

    def exec(self):
        return 0

    def accept(self):
        self.accepted += 1


def test_stock_detail_modify_and_remove(qapp, database, monkeypatch):
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO investment_stocks (ticker, company_name, notes) VALUES ('F', 'Ford', 'Review')"
        )
    page = InvestingPage(database)
    monkeypatch.setattr(stocks, "SecurityDetailDialog", FakeDetailDialog)
    FakeDetailDialog.instances.clear()
    index = page.stocks_table.model().index(0, 0)
    page._open_stock_details(index)
    dialog = FakeDetailDialog.instances[-1]
    assert dialog.args[1:6] == ("stock", 1, "Ford", "F", "Review")

    monkeypatch.setattr(page, "_modify_stock_by_id", lambda *args: False)
    dialog.modify_requested.callback()
    assert dialog.accepted == 0
    monkeypatch.setattr(page, "_modify_stock_by_id", lambda *args: True)
    dialog.modify_requested.callback()
    assert dialog.accepted == 1

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)
    dialog.remove_requested.callback()
    assert page.stocks_table.rowCount() == 1
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    dialog.remove_requested.callback()
    assert page.stocks_table.rowCount() == 0
    assert dialog.accepted == 2

    page._open_stock_details(SimpleNamespace(row=lambda: 99))
    page.stocks_table.insertRow(0)
    stale = QTableWidgetItem("Missing")
    stale.setData(stocks.STOCK_ID_ROLE, 999)
    page.stocks_table.setItem(0, 0, stale)
    page._open_stock_details(page.stocks_table.model().index(0, 0))


def test_mutual_fund_detail_modify_and_remove(qapp, database, monkeypatch):
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO investment_mutual_funds (symbol, fund_name, notes)
            VALUES ('VFIAX', 'Vanguard', 'Review')
            """
        )
    page = InvestingPage(database)
    monkeypatch.setattr(mutual_funds, "SecurityDetailDialog", FakeDetailDialog)
    FakeDetailDialog.instances.clear()
    index = page.mutual_funds_table.model().index(0, 0)
    page._open_mutual_fund_details(index)
    dialog = FakeDetailDialog.instances[-1]
    assert dialog.args[1:6] == ("mutual_fund", 1, "Vanguard", "VFIAX", "Review")

    monkeypatch.setattr(page, "_modify_mutual_fund_by_id", lambda *args: False)
    dialog.modify_requested.callback()
    monkeypatch.setattr(page, "_modify_mutual_fund_by_id", lambda *args: True)
    dialog.modify_requested.callback()
    assert dialog.accepted == 1

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)
    dialog.remove_requested.callback()
    assert page.mutual_funds_table.rowCount() == 1
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    dialog.remove_requested.callback()
    assert page.mutual_funds_table.rowCount() == 0

    page._open_mutual_fund_details(SimpleNamespace(row=lambda: 99))
    page.mutual_funds_table.insertRow(0)
    stale = QTableWidgetItem("Missing")
    stale.setData(mutual_funds.MUTUAL_FUND_ID_ROLE, 999)
    page.mutual_funds_table.setItem(0, 0, stale)
    page._open_mutual_fund_details(page.mutual_funds_table.model().index(0, 0))
