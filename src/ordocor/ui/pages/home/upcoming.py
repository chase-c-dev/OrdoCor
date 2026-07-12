from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from .models import UPCOMING_DATE_ROLE


class UpcomingMixin:
    def _upcoming_panel(self) -> QFrame:
        panel = self._panel("upcomingPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Upcoming")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")

        caption = QLabel("Calendar items due in the next 7 days")
        caption.setStyleSheet("color: #B6A896; font-size: 12px;")

        self.upcoming_list = QListWidget()
        self.upcoming_list.itemDoubleClicked.connect(self._open_upcoming_item_date)

        layout.addWidget(title)
        layout.addWidget(caption)
        layout.addWidget(self.upcoming_list, stretch=1)
        return panel

    def _load_upcoming(self) -> None:
        self.upcoming_list.clear()

        today = date.today()
        end_date = today + timedelta(days=7)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT item_date, title, notes
                    FROM calendar_items
                    WHERE item_date BETWEEN ? AND ?
                    ORDER BY item_date, created_at, id
                    """,
                (today.isoformat(), end_date.isoformat()),
            ).fetchall()

        if not rows:
            empty_item = QListWidgetItem("Nothing scheduled in the next 7 days")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsSelectable)
            self.upcoming_list.addItem(empty_item)
            return

        for row in rows:
            item_date = date.fromisoformat(row["item_date"])
            label = f"{item_date.strftime('%a, %b')} {item_date.day} - {row['title']}"
            item = QListWidgetItem(label)
            item.setData(UPCOMING_DATE_ROLE, row["item_date"])
            item.setToolTip(row["notes"] or row["title"])
            self.upcoming_list.addItem(item)

    def _open_upcoming_item_date(self, item: QListWidgetItem) -> None:
        item_date = item.data(UPCOMING_DATE_ROLE)
        if not item_date:
            return

        self._open_day(date.fromisoformat(item_date))
