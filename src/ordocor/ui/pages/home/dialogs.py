from __future__ import annotations

import calendar
from datetime import date

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database

from .models import CALENDAR_ITEM_ID_ROLE, CalendarItem


class TextItemDialog(QDialog):
    def __init__(
        self,
        title: str,
        parent: QWidget,
        item_title: str = "",
        notes: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title_label = QLabel("Title")
        self.title_input = QLineEdit(item_title)
        self.title_input.setPlaceholderText("Enter a title")

        notes_label = QLabel("Notes")
        self.notes_input = QTextEdit(notes)
        self.notes_input.setPlaceholderText("Optional notes")
        self.notes_input.setFixedHeight(110)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_input)
        layout.addWidget(buttons)

    def item(self) -> CalendarItem:
        return CalendarItem(
            id=None,
            title=self.title_input.text().strip(),
            notes=self.notes_input.toPlainText().strip(),
        )


class CalendarDayDialog(QDialog):
    def __init__(self, database: Database, selected_date: date, parent: QWidget) -> None:
        super().__init__(parent)
        self.database = database
        self.selected_date = selected_date
        self.setWindowTitle(
            f"{calendar.month_name[selected_date.month]} {selected_date.day}, {selected_date.year}"
        )
        self.setMinimumSize(480, 360)
        self._build_ui()
        self._load_items()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel(self.selected_date.strftime("%A, %B %d, %Y"))
        heading.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")

        self.items = QListWidget()

        actions = QHBoxLayout()
        add_button = QPushButton("Add")
        edit_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        close_button = QPushButton("Close")

        add_button.clicked.connect(self._add_item)
        edit_button.clicked.connect(self._edit_item)
        remove_button.clicked.connect(self._remove_item)
        close_button.clicked.connect(self.accept)

        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(remove_button)
        actions.addStretch()
        actions.addWidget(close_button)

        layout.addWidget(heading)
        layout.addWidget(self.items, stretch=1)
        layout.addLayout(actions)

    def _load_items(self) -> None:
        self.items.clear()
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, notes
                FROM calendar_items
                WHERE item_date = ?
                ORDER BY created_at, id
                """,
                (self.selected_date.isoformat(),),
            ).fetchall()

        for row in rows:
            item = QListWidgetItem(row["title"])
            item.setData(CALENDAR_ITEM_ID_ROLE, row["id"])
            item.setToolTip(row["notes"] or row["title"])
            self.items.addItem(item)

    def _add_item(self) -> None:
        dialog = TextItemDialog("Add Calendar Item", self)
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.item()
        if not item.title:
            QMessageBox.warning(self, "Missing Title", "Calendar items need a title.")
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO calendar_items (item_date, title, notes)
                VALUES (?, ?, ?)
                """,
                (self.selected_date.isoformat(), item.title, item.notes),
            )
        self._load_items()

    def _edit_item(self) -> None:
        current = self.items.currentItem()
        if current is None:
            return

        item_id = current.data(CALENDAR_ITEM_ID_ROLE)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT title, notes FROM calendar_items WHERE id = ?",
                (item_id,),
            ).fetchone()

        if row is None:
            return

        dialog = TextItemDialog("Modify Calendar Item", self, row["title"], row["notes"] or "")
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.item()
        if not item.title:
            QMessageBox.warning(self, "Missing Title", "Calendar items need a title.")
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE calendar_items
                SET title = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (item.title, item.notes, item_id),
            )
        self._load_items()

    def _remove_item(self) -> None:
        current = self.items.currentItem()
        if current is None:
            return

        item_id = current.data(CALENDAR_ITEM_ID_ROLE)
        with self.database.connect() as connection:
            connection.execute("DELETE FROM calendar_items WHERE id = ?", (item_id,))
        self._load_items()
