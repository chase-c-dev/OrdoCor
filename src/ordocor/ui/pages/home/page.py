from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ordocor.data.database import Database

from .calendar_view import CalendarMixin
from .todos import TodoMixin
from .upcoming import UpcomingMixin


class HomePage(TodoMixin, UpcomingMixin, CalendarMixin, QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.current_year = date.today().year
        self._loading_todos = False
        self._build_ui()
        self._load_todos()
        self._load_upcoming()
        self._render_calendar()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        heading = QLabel("Home")
        heading.setStyleSheet("color: #F3E7C9; font-size: 30px; font-weight: 800;")

        content = QHBoxLayout()
        content.setSpacing(18)

        left_column = QVBoxLayout()
        left_column.setSpacing(18)
        left_column.addWidget(self._todo_panel(), stretch=3)
        left_column.addWidget(self._upcoming_panel(), stretch=2)

        content.addLayout(left_column, stretch=1)
        content.addWidget(self._calendar_panel(), stretch=2)

        layout.addWidget(heading)
        layout.addLayout(content, stretch=1)

    def _panel(self, object_name: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName(object_name)
        panel.setStyleSheet(
            f"""
                QFrame#{object_name} {{
                    background: #231C20;
                    border: 1px solid #665451;
                    border-radius: 8px;
                }}
                """
        )
        return panel
