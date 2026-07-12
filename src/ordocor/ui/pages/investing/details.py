from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCharts import QChart, QChartView, QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import (
    QDate,
    QDateTime,
    QMargins,
    QPointF,
    Qt,
    QTime,
    QThreadPool,
    QTimeZone,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database
from ordocor.services.market_data import HistoricalPrice, MarketHistoryWorker
from ordocor.ui.theme import themed_stylesheet


RANGE_OPTIONS = {
    "1D": ("days", 1),
    "5D": ("days", 5),
    "1M": ("months", 1),
    "6M": ("months", 6),
    "1Y": ("months", 12),
    "3Y": ("months", 36),
    "5Y": ("months", 60),
}
SECURITY_TABLES = {
    "stock": "investment_stocks",
    "mutual_fund": "investment_mutual_funds",
}


class PriceHistoryChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._prices: tuple[HistoricalPrice, ...] = ()
        self._range = "5Y"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Range"))
        self.range_group = QButtonGroup(self)
        for label in RANGE_OPTIONS:
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=label: self.set_range(value))
            self.range_group.addButton(button)
            range_row.addWidget(button)
            if label == "5Y":
                button.setChecked(True)
        range_row.addStretch()

        self.hover_label = QLabel("Hover over the chart to inspect a closing price.")
        self.hover_label.setStyleSheet("color: #D2C4AA; font-size: 12px;")
        self.series = QLineSeries()
        self.series.setPen(QPen(QColor(themed_stylesheet("#C0A361")), 2))
        self.series.hovered.connect(self._show_hover)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.legend().hide()
        self.chart.setBackgroundVisible(False)
        self.chart.setPlotAreaBackgroundVisible(False)
        self.chart.setMargins(QMargins(0, 4, 0, 0))

        self.date_axis = QDateTimeAxis()
        self.date_axis.setFormat("MMM yyyy")
        self.date_axis.setLabelsColor(QColor(themed_stylesheet("#D2C4AA")))
        self.value_axis = QValueAxis()
        self.value_axis.setLabelFormat("$%.2f")
        self.value_axis.setLabelsColor(QColor(themed_stylesheet("#D2C4AA")))
        self.chart.addAxis(self.date_axis, Qt.AlignBottom)
        self.chart.addAxis(self.value_axis, Qt.AlignLeft)
        self.series.attachAxis(self.date_axis)
        self.series.attachAxis(self.value_axis)

        view = QChartView(self.chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(280)
        layout.addLayout(range_row)
        layout.addWidget(self.hover_label)
        layout.addWidget(view)

    def set_prices(self, prices: Iterable[HistoricalPrice]) -> None:
        self._prices = tuple(prices)
        self._render()

    def set_range(self, range_name: str) -> None:
        if range_name not in RANGE_OPTIONS:
            return
        self._range = range_name
        self._render()

    def _render(self) -> None:
        if not self._prices:
            self.series.clear()
            return

        end_date = QDate.fromString(self._prices[-1].price_date, "yyyy-MM-dd")
        range_unit, range_value = RANGE_OPTIONS[self._range]
        start_date = (
            end_date.addDays(-range_value)
            if range_unit == "days"
            else end_date.addMonths(-range_value)
        )
        visible = [
            price
            for price in self._prices
            if QDate.fromString(price.price_date, "yyyy-MM-dd") >= start_date
        ]
        points = [
            QPointF(
                QDateTime(
                    QDate.fromString(price.price_date, "yyyy-MM-dd"),
                    QTime(0, 0),
                    QTimeZone.UTC,
                ).toMSecsSinceEpoch(),
                price.close_price,
            )
            for price in visible
        ]
        self.series.replace(points)
        values = [price.close_price for price in visible]
        minimum, maximum = min(values), max(values)
        padding = max((maximum - minimum) * 0.08, maximum * 0.01, 0.01)
        self.value_axis.setRange(max(0, minimum - padding), maximum + padding)
        self.date_axis.setRange(
            QDateTime(
                QDate.fromString(visible[0].price_date, "yyyy-MM-dd"),
                QTime(0, 0),
                QTimeZone.UTC,
            ),
            QDateTime(
                QDate.fromString(visible[-1].price_date, "yyyy-MM-dd"),
                QTime(0, 0),
                QTimeZone.UTC,
            ),
        )

    def _show_hover(self, point: QPointF, state: bool) -> None:
        if not state:
            self.hover_label.setText("Hover over the chart to inspect a closing price.")
            return
        date = QDateTime.fromMSecsSinceEpoch(int(point.x()), QTimeZone.UTC).date()
        self.hover_label.setText(f"{date.toString('MMM d, yyyy')}  |  ${point.y():,.2f}")


class SecurityDetailDialog(QDialog):
    modify_requested = Signal()
    remove_requested = Signal()

    def __init__(
        self,
        database: Database,
        security_kind: str,
        security_id: int,
        name: str,
        symbol: str,
        notes: str,
        parent: QWidget | None = None,
        auto_refresh: bool = True,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.security_kind = security_kind
        self.security_id = security_id
        self.symbol = symbol
        self._history_worker = None
        self._thread_pool = QThreadPool.globalInstance()
        self.setWindowTitle(f"{name} ({symbol})")
        self.resize(900, 720)

        layout = QVBoxLayout(self)
        heading = QLabel(name)
        heading.setStyleSheet("color: #F3E7C9; font-size: 22px; font-weight: 800;")
        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet("color: #B6A896;")

        chart_header = QHBoxLayout()
        chart_header.addWidget(QLabel("Price History"))
        chart_header.addStretch()
        self.refresh_chart_button = QPushButton("Refresh Chart")
        self.refresh_chart_button.clicked.connect(self._refresh_history)
        chart_header.addWidget(self.refresh_chart_button)
        self.history_status = QLabel("Showing cached history.")
        self.history_status.setStyleSheet("color: #9B8F83; font-size: 12px;")
        self.history_chart = PriceHistoryChart()

        notes_label = QLabel("Notes")
        self.notes_input = QTextEdit(notes)
        self.notes_input.setPlaceholderText("Research, strategy, reminders, or review notes...")
        self.notes_input.setMaximumHeight(150)
        self.notes_status = QLabel("")
        self.notes_status.setStyleSheet("color: #9B8F83; font-size: 12px;")
        self.notes_status.setText("Notes save automatically when this window closes.")

        actions = QHBoxLayout()
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        modify_button.clicked.connect(self.modify_requested.emit)
        remove_button.clicked.connect(self.remove_requested.emit)
        actions.addStretch()
        actions.addWidget(modify_button)
        actions.addWidget(remove_button)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        layout.addWidget(heading)
        layout.addWidget(symbol_label)
        layout.addLayout(chart_header)
        layout.addWidget(self.history_status)
        layout.addWidget(self.history_chart, stretch=1)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.notes_status)
        layout.addLayout(actions)
        layout.addWidget(close_buttons)
        self._load_cached_history()
        if auto_refresh:
            QTimer.singleShot(0, self._refresh_history)

    def _table_name(self) -> str:
        return SECURITY_TABLES[self.security_kind]

    def _save_notes(self) -> None:
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE {self._table_name()} SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (self.notes_input.toPlainText(), self.security_id),
            )
        self.notes_status.setText("Notes saved.")

    def done(self, result: int) -> None:
        self._save_notes()
        super().done(result)

    def _load_cached_history(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT price_date, close_price
                FROM market_price_history
                WHERE symbol = ?
                ORDER BY price_date
                """,
                (self.symbol,),
            ).fetchall()
        prices = tuple(HistoricalPrice(row["price_date"], row["close_price"]) for row in rows)
        self.history_chart.set_prices(prices)
        if not prices:
            self.history_status.setText("No cached history. Refresh the chart while online.")

    def _refresh_history(self) -> None:
        if self._history_worker is not None:
            return
        self.refresh_chart_button.setEnabled(False)
        self.history_status.setText("Refreshing five years of price history...")
        worker = MarketHistoryWorker(self.symbol)
        worker.signals.completed.connect(self._history_refreshed)
        worker.signals.failed.connect(self._history_failed)
        self._history_worker = worker
        self._thread_pool.start(worker)

    def _history_refreshed(self, prices: tuple[HistoricalPrice, ...]) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM market_price_history WHERE symbol = ?", (self.symbol,))
            connection.executemany(
                """
                INSERT INTO market_price_history (symbol, price_date, close_price)
                VALUES (?, ?, ?)
                """,
                ((self.symbol, price.price_date, price.close_price) for price in prices),
            )
        self.history_chart.set_prices(prices)
        self.history_status.setText("Five-year price history updated.")
        self._finish_history_refresh()

    def _history_failed(self, error: str) -> None:
        self.history_status.setText(f"Could not refresh chart: {error}")
        self._finish_history_refresh()

    def _finish_history_refresh(self) -> None:
        self.refresh_chart_button.setEnabled(True)
        self._history_worker = None
