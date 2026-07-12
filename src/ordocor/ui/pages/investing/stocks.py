from __future__ import annotations

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ordocor.services.market_data import MarketDataWorker, MarketQuote

from .details import SecurityDetailDialog
from .table_config import configure_compact_market_table


STOCK_ID_ROLE = Qt.UserRole + 1
GAIN_COLOR = QColor("#66D98F")
LOSS_COLOR = QColor("#FF6B6B")


class StockDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        stock: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.name_input = QLineEdit(str(stock.get("stock_name", "")) if stock else "")
        self.name_input.setPlaceholderText("Example: Apple Inc.")

        self.ticker_input = QLineEdit(str(stock.get("ticker", "")) if stock else "")
        self.ticker_input.setPlaceholderText("Example: AAPL")

        self.purchase_date_input = QDateEdit()
        self.purchase_date_input.setCalendarPopup(True)
        self.purchase_date_input.setDisplayFormat("yyyy-MM-dd")
        if stock and stock.get("purchase_date"):
            self.purchase_date_input.setDate(
                self.purchase_date_input.date().fromString(
                    str(stock["purchase_date"]), "yyyy-MM-dd"
                )
            )

        self.purchase_price_input = self._money_input(stock, "purchase_price")
        self.shares_input = self._number_input(stock, "shares")
        self.target_sell_price_input = self._money_input(stock, "target_sell_price")

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Stock Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Ticker Symbol"), 1, 0)
        form.addWidget(self.ticker_input, 1, 1)
        form.addWidget(QLabel("Purchase Date"), 2, 0)
        form.addWidget(self.purchase_date_input, 2, 1)
        form.addWidget(QLabel("Purchase Price"), 3, 0)
        form.addWidget(self.purchase_price_input, 3, 1)
        form.addWidget(QLabel("Number of Shares"), 4, 0)
        form.addWidget(self.shares_input, 4, 1)
        form.addWidget(QLabel("Target Sell Price"), 5, 0)
        form.addWidget(self.target_sell_price_input, 5, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def stock_data(self) -> dict[str, object]:
        return {
            "stock_name": self.name_input.text().strip(),
            "ticker": self.ticker_input.text().strip().upper(),
            "purchase_date": self.purchase_date_input.date().toString("yyyy-MM-dd"),
            "purchase_price": self.purchase_price_input.value(),
            "shares": self.shares_input.value(),
            "target_sell_price": self.target_sell_price_input.value(),
        }

    def _money_input(self, stock: dict[str, object] | None, key: str) -> QDoubleSpinBox:
        input_widget = QDoubleSpinBox()
        input_widget.setRange(0, 1_000_000_000)
        input_widget.setDecimals(2)
        input_widget.setPrefix("$")
        input_widget.setValue(float(stock.get(key, 0) or 0) if stock else 0)
        return input_widget

    def _number_input(self, stock: dict[str, object] | None, key: str) -> QDoubleSpinBox:
        input_widget = QDoubleSpinBox()
        input_widget.setRange(0, 1_000_000_000)
        input_widget.setDecimals(6)
        input_widget.setValue(float(stock.get(key, 0) or 0) if stock else 0)
        return input_widget


class StocksMixin:
    def _stocks_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Stocks")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        self.market_refresh_button = QPushButton("Refresh Market Data")
        add_button.clicked.connect(self._add_stock)
        self.market_refresh_button.clicked.connect(self._refresh_market_data)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.market_refresh_button)
        header.addWidget(add_button)

        self.market_status = QLabel("Market data uses the last successful refresh.")
        self.market_status.setStyleSheet("color: #9B8F83; font-size: 12px;")
        market_help = QLabel(
            "Market data refreshes when this tab opens. Double-click a stock to open its chart, "
            "notes, and additional actions."
        )
        market_help.setWordWrap(True)
        market_help.setStyleSheet("color: #B6A896; font-size: 12px;")

        self.stocks_table = QTableWidget(0, 12)
        configure_compact_market_table(
            self.stocks_table,
            (
                "Name",
                "Ticker",
                "Buy Date",
                "Buy\nPrice",
                "Shares",
                "Cost\nBasis",
                "Target\nPrice",
                "Market\nPrice",
                "Market\nValue",
                "Gain\nLoss",
                "Return",
                "Dividend\nYield",
            ),
        )
        self.stocks_table.doubleClicked.connect(self._open_stock_details)

        layout.addLayout(header)
        layout.addWidget(self.market_status)
        layout.addWidget(market_help)
        layout.addWidget(self.stocks_table, stretch=1)
        self._market_thread_pool = QThreadPool.globalInstance()
        self._market_worker = None
        self._load_stocks()
        return page

    def _load_stocks(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, ticker, company_name, purchase_date, purchase_price, shares,
                           target_sell_price, market_price, dividend_yield, market_updated_at
                    FROM investment_stocks
                    ORDER BY company_name, ticker, id
                    """
            ).fetchall()

        self.stocks_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.stocks_table.insertRow(row_index)
            purchase_price = float(row["purchase_price"] or 0)
            shares = float(row["shares"] or 0)
            market_price = float(row["market_price"]) if row["market_price"] is not None else None
            cost_basis = purchase_price * shares
            market_value = market_price * shares if market_price is not None else None
            gain_loss = market_value - cost_basis if market_value is not None else None
            return_percentage = (
                ((market_price - purchase_price) / purchase_price) * 100
                if market_price is not None and purchase_price > 0
                else None
            )
            values = (
                row["company_name"] or "",
                row["ticker"] or "",
                row["purchase_date"] or "",
                self._money(purchase_price),
                self._number(shares),
                self._money(cost_basis),
                self._money(row["target_sell_price"]),
                self._optional_money(market_price),
                self._optional_money(market_value),
                self._optional_money(gain_loss, signed=True),
                self._optional_percent(return_percentage, signed=True),
                self._optional_percent(row["dividend_yield"]),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(STOCK_ID_ROLE, row["id"])
                if column == 7 and row["market_updated_at"]:
                    item.setToolTip(f"Updated: {row['market_updated_at']}")
                if column in (9, 10):
                    self._apply_performance_color(item, gain_loss)
                self.stocks_table.setItem(row_index, column, item)

    def _apply_performance_color(
        self,
        item: QTableWidgetItem,
        gain_loss: float | None,
    ) -> None:
        if gain_loss is None or gain_loss == 0:
            return
        item.setForeground(QBrush(GAIN_COLOR if gain_loss > 0 else LOSS_COLOR))

    def _add_stock(self) -> None:
        dialog = StockDialog(self, "Add Stock")
        if dialog.exec() != QDialog.Accepted:
            return

        stock = dialog.stock_data()
        if not self._validate_stock(stock):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    INSERT INTO investment_stocks (
                        ticker, company_name, purchase_date, purchase_price, shares, target_sell_price
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                (
                    stock["ticker"],
                    stock["stock_name"],
                    stock["purchase_date"],
                    stock["purchase_price"],
                    stock["shares"],
                    stock["target_sell_price"],
                ),
            )
        self._load_stocks()

    def _modify_stock(self) -> None:
        stock_id = self._selected_stock_id()
        if stock_id is None:
            return
        self._modify_stock_by_id(stock_id, self)

    def _modify_stock_by_id(self, stock_id: int, parent: QWidget) -> bool:

        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT id, ticker, company_name AS stock_name, purchase_date,
                           purchase_price, shares, target_sell_price
                    FROM investment_stocks
                    WHERE id = ?
                    """,
                (stock_id,),
            ).fetchone()

        if row is None:
            return False

        dialog = StockDialog(parent, "Modify Stock", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return False

        stock = dialog.stock_data()
        if not self._validate_stock(stock):
            return False

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE investment_stocks
                    SET ticker = ?,
                        company_name = ?,
                        purchase_date = ?,
                        purchase_price = ?,
                        shares = ?,
                        target_sell_price = ?,
                        market_price = NULL,
                        dividend_yield = NULL,
                        market_updated_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (
                    stock["ticker"],
                    stock["stock_name"],
                    stock["purchase_date"],
                    stock["purchase_price"],
                    stock["shares"],
                    stock["target_sell_price"],
                    stock_id,
                ),
            )
        self._load_stocks()
        return True

    def _open_stock_details(self, index) -> None:
        item = self.stocks_table.item(index.row(), 0)
        if item is None:
            return
        stock_id = item.data(STOCK_ID_ROLE)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT company_name, ticker, notes FROM investment_stocks WHERE id = ?",
                (stock_id,),
            ).fetchone()
        if row is None:
            return

        dialog = SecurityDetailDialog(
            self.database,
            "stock",
            stock_id,
            row["company_name"] or row["ticker"],
            row["ticker"],
            row["notes"] or "",
            self,
        )
        dialog.modify_requested.connect(lambda: self._modify_stock_from_details(stock_id, dialog))
        dialog.remove_requested.connect(lambda: self._remove_stock_from_details(stock_id, dialog))
        dialog.exec()

    def _modify_stock_from_details(self, stock_id: int, dialog: QDialog) -> None:
        if self._modify_stock_by_id(stock_id, dialog):
            dialog.accept()

    def _remove_stock_from_details(self, stock_id: int, dialog: QDialog) -> None:
        confirmed = QMessageBox.question(
            dialog,
            "Remove Stock",
            "Remove this stock and its saved notes?",
        )
        if confirmed != QMessageBox.Yes:
            return
        with self.database.connect() as connection:
            connection.execute("DELETE FROM investment_stocks WHERE id = ?", (stock_id,))
        self._load_stocks()
        dialog.accept()

    def _refresh_market_data(self) -> None:
        if self._market_worker is not None:
            return
        with self.database.connect() as connection:
            tickers = tuple(
                row["ticker"]
                for row in connection.execute(
                    "SELECT DISTINCT ticker FROM investment_stocks WHERE TRIM(ticker) != ''"
                )
            )

        if not tickers:
            self.market_status.setText("Add a stock before refreshing market data.")
            return

        self.market_refresh_button.setEnabled(False)
        self.market_status.setText("Refreshing market prices and dividend yields...")
        worker = MarketDataWorker(tickers)
        worker.signals.completed.connect(self._market_data_refreshed)
        self._market_worker = worker
        self._market_thread_pool.start(worker)

    def _market_data_refreshed(
        self,
        quotes: dict[str, MarketQuote],
        errors: dict[str, str],
    ) -> None:
        if quotes:
            with self.database.connect() as connection:
                for quote in quotes.values():
                    connection.execute(
                        """
                        UPDATE investment_stocks
                        SET market_price = ?, dividend_yield = ?, market_updated_at = ?
                        WHERE ticker = ?
                        """,
                        (
                            quote.market_price,
                            quote.dividend_yield,
                            quote.fetched_at,
                            quote.ticker,
                        ),
                    )

        self._load_stocks()
        self.market_refresh_button.setEnabled(True)
        if errors and quotes:
            self.market_status.setText(
                f"Updated {len(quotes)} ticker(s); {len(errors)} could not be refreshed."
            )
        elif errors:
            self.market_status.setText(
                "Market data is unavailable. Showing the last successful refresh."
            )
        else:
            self.market_status.setText(f"Updated market data for {len(quotes)} ticker(s).")
        self._market_worker = None

    def _remove_stock(self) -> None:
        stock_id = self._selected_stock_id()
        if stock_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM investment_stocks WHERE id = ?", (stock_id,))
        self._load_stocks()

    def _selected_stock_id(self) -> int | None:
        selected_items = self.stocks_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.stocks_table.item(row, 0)
        return item.data(STOCK_ID_ROLE) if item else None

    def _validate_stock(self, stock: dict[str, object]) -> bool:
        if not stock["stock_name"] or not stock["ticker"]:
            QMessageBox.warning(
                self, "Missing Stock Details", "Stock name and ticker symbol are required."
            )
            return False
        return True
