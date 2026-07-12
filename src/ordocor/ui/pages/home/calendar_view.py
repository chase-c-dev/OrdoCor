from __future__ import annotations

import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ordocor.ui.design_config import CALENDAR_DAY_BUTTON
from ordocor.ui.theme import themed_stylesheet

from .dialogs import CalendarDayDialog


class CalendarMixin:
    def _calendar_panel(self) -> QFrame:
        panel = self._panel("calendarPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        previous_button = QPushButton("<")
        next_button = QPushButton(">")
        previous_button.setFixedWidth(42)
        next_button.setFixedWidth(42)
        previous_button.clicked.connect(lambda: self._change_year(-1))
        next_button.clicked.connect(lambda: self._change_year(1))

        self.year_label = QLabel()
        self.year_label.setAlignment(Qt.AlignCenter)
        self.year_label.setStyleSheet("color: #F3E7C9; font-size: 22px; font-weight: 800;")

        header.addWidget(previous_button)
        header.addWidget(self.year_label, stretch=1)
        header.addWidget(next_button)

        self.calendar_content = QWidget()
        self.calendar_grid = QGridLayout(self.calendar_content)
        self.calendar_grid.setSpacing(14)
        self.calendar_grid.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.calendar_content)

        layout.addLayout(header)
        layout.addWidget(scroll_area, stretch=1)
        return panel

    def _change_year(self, offset: int) -> None:
        self.current_year += offset
        self._render_calendar()

    def _render_calendar(self) -> None:
        self.year_label.setText(str(self.current_year))
        self._clear_layout(self.calendar_grid)
        item_counts = self._calendar_item_counts()

        for month_index in range(1, 13):
            row = (month_index - 1) // 3
            column = (month_index - 1) % 3
            self.calendar_grid.addWidget(
                self._month_widget(month_index, item_counts),
                row,
                column,
            )

    def _month_widget(self, month: int, item_counts: dict[str, int]) -> QFrame:
        month_frame = self._panel("monthPanel")
        layout = QVBoxLayout(month_frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel(calendar.month_name[month])
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #F3E7C9; font-size: 16px; font-weight: 800;")

        day_grid = QGridLayout()
        day_grid.setSpacing(4)

        for column, label in enumerate(("M", "T", "W", "T", "F", "S", "S")):
            day_label = QLabel(label)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet("color: #9B8F83; font-size: 11px; font-weight: 700;")
            day_grid.addWidget(day_label, 0, column)

        for week_index, week in enumerate(
            calendar.monthcalendar(self.current_year, month), start=1
        ):
            for column, day_number in enumerate(week):
                if day_number == 0:
                    day_grid.addWidget(QLabel(""), week_index, column)
                    continue

                item_date = date(self.current_year, month, day_number)
                button = QPushButton(str(day_number))
                button.setFixedSize(
                    CALENDAR_DAY_BUTTON["width"],
                    CALENDAR_DAY_BUTTON["height"],
                )
                button.clicked.connect(lambda _checked=False, day=item_date: self._open_day(day))
                button.setStyleSheet(self._day_button_stylesheet(item_date, item_counts))
                day_grid.addWidget(button, week_index, column)

        layout.addWidget(title)
        layout.addLayout(day_grid)
        return month_frame

    def _open_day(self, selected_date: date) -> None:
        dialog = CalendarDayDialog(self.database, selected_date, self)
        dialog.exec()
        self._render_calendar()
        self._load_upcoming()

    def _calendar_item_counts(self) -> dict[str, int]:
        start = date(self.current_year, 1, 1).isoformat()
        end = date(self.current_year, 12, 31).isoformat()
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT item_date, COUNT(*) AS item_count
                    FROM calendar_items
                    WHERE item_date BETWEEN ? AND ?
                    GROUP BY item_date
                    """,
                (start, end),
            ).fetchall()

        return {row["item_date"]: row["item_count"] for row in rows}

    def _day_button_stylesheet(self, item_date: date, item_counts: dict[str, int]) -> str:
        button = CALENDAR_DAY_BUTTON
        date_key = item_date.isoformat()
        if date_key in item_counts:
            return themed_stylesheet(f"""
                    QPushButton {{
                        background: #6F3944;
                        border: {button["border_width"]}px solid #9E5D68;
                        border-radius: {button["radius"]}px;
                        color: #F7EDCF;
                        font-weight: {button["font_weight"]};
                        padding: {button["padding"]};
                    }}
                """)
        if item_date == date.today():
            return themed_stylesheet(f"""
                    QPushButton {{
                        background: #33292D;
                        border: {button["border_width"]}px solid #B4A06B;
                        border-radius: {button["radius"]}px;
                        color: #F3E7C9;
                        font-weight: {button["font_weight"]};
                        padding: {button["padding"]};
                    }}
                """)
        return themed_stylesheet(f"""
                QPushButton {{
                    background: #191518;
                    border: {button["border_width"]}px solid #665451;
                    border-radius: {button["radius"]}px;
                    color: #E2D4B7;
                    padding: {button["padding"]};
                }}
                QPushButton:hover {{
                    background: #3B2D32;
                    border: {button["border_width"]}px solid #C0A361;
                }}
            """)

    def _clear_layout(self, layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
