from __future__ import annotations


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .dialogs import TextItemDialog
from .models import TODO_ID_ROLE


class TodoMixin:
    def _todo_panel(self) -> QFrame:
        panel = self._panel("todoPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("TODO List")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")

        self.todo_list = QListWidget()
        self.todo_list.itemChanged.connect(self._toggle_todo)
        self.todo_list.itemDoubleClicked.connect(lambda _item: self._edit_todo())

        actions = QGridLayout()
        actions.setSpacing(8)
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_todo)
        modify_button.clicked.connect(self._edit_todo)
        remove_button.clicked.connect(self._remove_todo)
        actions.addWidget(add_button, 0, 0)
        actions.addWidget(modify_button, 0, 1)
        actions.addWidget(remove_button, 1, 0, 1, 2)

        layout.addWidget(title)
        layout.addWidget(self.todo_list, stretch=1)
        layout.addLayout(actions)
        return panel

    def _load_todos(self) -> None:
        self._loading_todos = True
        self.todo_list.clear()

        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, title, notes, is_completed
                    FROM todo_items
                    ORDER BY is_completed, created_at, id
                    """
            ).fetchall()

        for row in rows:
            item = QListWidgetItem(row["title"])
            item.setData(TODO_ID_ROLE, row["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if row["is_completed"] else Qt.Unchecked)
            item.setToolTip(row["notes"] or row["title"])
            if row["is_completed"]:
                item.setForeground(Qt.gray)
            self.todo_list.addItem(item)

        self._loading_todos = False

    def _add_todo(self) -> None:
        dialog = TextItemDialog("Add TODO", self)
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.item()
        if not item.title:
            QMessageBox.warning(self, "Missing Title", "TODO items need a title.")
            return

        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO todo_items (title, notes) VALUES (?, ?)",
                (item.title, item.notes),
            )
        self._load_todos()

    def _edit_todo(self) -> None:
        current = self.todo_list.currentItem()
        if current is None:
            return

        todo_id = current.data(TODO_ID_ROLE)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT title, notes FROM todo_items WHERE id = ?",
                (todo_id,),
            ).fetchone()

        if row is None:
            return

        dialog = TextItemDialog("Modify TODO", self, row["title"], row["notes"] or "")
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.item()
        if not item.title:
            QMessageBox.warning(self, "Missing Title", "TODO items need a title.")
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE todo_items
                    SET title = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (item.title, item.notes, todo_id),
            )
        self._load_todos()

    def _remove_todo(self) -> None:
        current = self.todo_list.currentItem()
        if current is None:
            return

        todo_id = current.data(TODO_ID_ROLE)
        with self.database.connect() as connection:
            connection.execute("DELETE FROM todo_items WHERE id = ?", (todo_id,))
        self._load_todos()

    def _toggle_todo(self, item: QListWidgetItem) -> None:
        if self._loading_todos:
            return

        is_completed = 1 if item.checkState() == Qt.Checked else 0
        todo_id = item.data(TODO_ID_ROLE)
        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE todo_items
                    SET is_completed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (is_completed, todo_id),
            )
        self._load_todos()
