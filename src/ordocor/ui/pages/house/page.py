from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database
from ordocor.ui.pages.property_dialogs import FieldSpec, PropertyFormDialog


HOUSE_REMINDER_ID_ROLE = Qt.UserRole + 1
HOUSE_MAINTENANCE_ID_ROLE = Qt.UserRole + 2
HOUSE_IMPROVEMENT_ID_ROLE = Qt.UserRole + 3

REMINDER_FIELDS = (
    FieldSpec("name", "Bill or Reminder"),
    FieldSpec("reminder_type", "Type"),
    FieldSpec("due_date", "Due Date", "date"),
    FieldSpec("amount", "Amount", "money"),
    FieldSpec("notes", "Notes", "multiline"),
)
MAINTENANCE_FIELDS = (
    FieldSpec("title", "Maintenance Item"),
    FieldSpec("frequency", "Frequency"),
    FieldSpec("due_date", "Due Date", "date"),
    FieldSpec("video_url", "YouTube or Reference Link"),
    FieldSpec("notes", "Notes", "multiline"),
)
IMPROVEMENT_FIELDS = (
    FieldSpec("name", "Improvement"),
    FieldSpec("priority", "Priority"),
    FieldSpec("estimated_cost", "Estimated Cost", "money"),
    FieldSpec("notes", "Notes", "multiline"),
)


class HouseReminderDialog(PropertyFormDialog):
    def __init__(self, parent: QWidget | None, title: str, item: dict[str, object] | None = None):
        super().__init__(parent, title, REMINDER_FIELDS, item)

    def reminder_data(self) -> dict[str, object]:
        return self.form_data()


class HouseMaintenanceDialog(PropertyFormDialog):
    def __init__(self, parent: QWidget | None, title: str, item: dict[str, object] | None = None):
        super().__init__(parent, title, MAINTENANCE_FIELDS, item)

    def maintenance_data(self) -> dict[str, object]:
        return self.form_data()


class HouseImprovementDialog(PropertyFormDialog):
    def __init__(self, parent: QWidget | None, title: str, item: dict[str, object] | None = None):
        super().__init__(parent, title, IMPROVEMENT_FIELDS, item)

    def improvement_data(self) -> dict[str, object]:
        return self.form_data()


class HousePage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self._load_all()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("House")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        panel = self._panel("housePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._reminders_tab(), "Tax & Insurance")
        self.tabs.addTab(self._maintenance_tab(), "Maintenance")
        self.tabs.addTab(self._improvements_tab(), "Improvements")
        panel_layout.addWidget(self.tabs)

        layout.addWidget(heading)
        layout.addWidget(panel, stretch=1)

    def _reminders_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(
            self._action_row(self._add_reminder, self._modify_reminder, self._remove_reminder)
        )
        self.reminders_table = QTableWidget(0, 5)
        self.reminders_table.setHorizontalHeaderLabels(
            ("Reminder", "Type", "Due Date", "Amount", "Notes")
        )
        self._configure_table(self.reminders_table)
        self.reminders_table.doubleClicked.connect(self._modify_reminder)
        layout.addWidget(self.reminders_table, stretch=1)
        return page

    def _maintenance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = self._action_row(
            self._add_maintenance, self._modify_maintenance, self._remove_maintenance
        )
        open_button = QPushButton("Open Link")
        open_button.clicked.connect(self._open_maintenance_link)
        header.addWidget(open_button)
        self.maintenance_table = QTableWidget(0, 5)
        self.maintenance_table.setHorizontalHeaderLabels(
            ("Item", "Frequency", "Due Date", "Link", "Notes")
        )
        self._configure_table(self.maintenance_table)
        self.maintenance_table.doubleClicked.connect(self._modify_maintenance)
        layout.addLayout(header)
        layout.addWidget(self.maintenance_table, stretch=1)
        return page

    def _improvements_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(
            self._action_row(
                self._add_improvement, self._modify_improvement, self._remove_improvement
            )
        )
        self.improvements_table = QTableWidget(0, 4)
        self.improvements_table.setHorizontalHeaderLabels(
            ("Improvement", "Priority", "Cost", "Notes")
        )
        self._configure_table(self.improvements_table)
        self.improvements_table.doubleClicked.connect(self._modify_improvement)
        layout.addWidget(self.improvements_table, stretch=1)
        return page

    def _load_all(self) -> None:
        self._load_reminders()
        self._load_maintenance()
        self._load_improvements()

    def _load_reminders(self) -> None:
        rows = self._rows(
            "SELECT id, name, reminder_type, due_date, amount, notes FROM house_reminders ORDER BY due_date, name, id"
        )
        self.reminders_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.reminders_table.insertRow(row_index)
            values = (
                row["name"],
                row["reminder_type"],
                row["due_date"],
                self._money(row["amount"]),
                self._preview(row["notes"]),
            )
            self._set_row(
                self.reminders_table, row_index, values, HOUSE_REMINDER_ID_ROLE, row["id"]
            )

    def _add_reminder(self) -> None:
        self._add_record(
            HouseReminderDialog,
            "Add House Reminder",
            "reminder_data",
            "house_reminders",
            ("name", "reminder_type", "due_date", "amount", "notes"),
            "name",
            self._load_reminders,
            "Reminder name is required.",
        )

    def _modify_reminder(self) -> None:
        self._modify_record(
            self.reminders_table,
            HOUSE_REMINDER_ID_ROLE,
            HouseReminderDialog,
            "Modify House Reminder",
            "reminder_data",
            "house_reminders",
            ("name", "reminder_type", "due_date", "amount", "notes"),
            "name",
            self._load_reminders,
            "Reminder name is required.",
        )

    def _remove_reminder(self) -> None:
        self._remove_record(
            self.reminders_table, HOUSE_REMINDER_ID_ROLE, "house_reminders", self._load_reminders
        )

    def _load_maintenance(self) -> None:
        rows = self._rows(
            """
            SELECT id, title, frequency, due_date, video_url, notes
            FROM house_maintenance
            ORDER BY due_date, title, id
            """
        )
        self.maintenance_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.maintenance_table.insertRow(row_index)
            values = (
                row["title"],
                row["frequency"],
                row["due_date"],
                row["video_url"],
                self._preview(row["notes"]),
            )
            self._set_row(
                self.maintenance_table, row_index, values, HOUSE_MAINTENANCE_ID_ROLE, row["id"]
            )

    def _add_maintenance(self) -> None:
        self._add_record(
            HouseMaintenanceDialog,
            "Add House Maintenance",
            "maintenance_data",
            "house_maintenance",
            ("title", "frequency", "due_date", "video_url", "notes"),
            "title",
            self._load_maintenance,
            "Maintenance item is required.",
        )

    def _modify_maintenance(self) -> None:
        self._modify_record(
            self.maintenance_table,
            HOUSE_MAINTENANCE_ID_ROLE,
            HouseMaintenanceDialog,
            "Modify House Maintenance",
            "maintenance_data",
            "house_maintenance",
            ("title", "frequency", "due_date", "video_url", "notes"),
            "title",
            self._load_maintenance,
            "Maintenance item is required.",
        )

    def _remove_maintenance(self) -> None:
        self._remove_record(
            self.maintenance_table,
            HOUSE_MAINTENANCE_ID_ROLE,
            "house_maintenance",
            self._load_maintenance,
        )

    def _open_maintenance_link(self) -> None:
        row = self.maintenance_table.currentRow()
        item = self.maintenance_table.item(row, 3) if row >= 0 else None
        url = item.text().strip() if item else ""
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _load_improvements(self) -> None:
        rows = self._rows(
            "SELECT id, name, priority, estimated_cost, notes FROM house_improvements ORDER BY priority, name, id"
        )
        self.improvements_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.improvements_table.insertRow(row_index)
            values = (
                row["name"],
                row["priority"],
                self._money(row["estimated_cost"]),
                self._preview(row["notes"]),
            )
            self._set_row(
                self.improvements_table, row_index, values, HOUSE_IMPROVEMENT_ID_ROLE, row["id"]
            )

    def _add_improvement(self) -> None:
        self._add_record(
            HouseImprovementDialog,
            "Add House Improvement",
            "improvement_data",
            "house_improvements",
            ("name", "priority", "estimated_cost", "notes"),
            "name",
            self._load_improvements,
            "Improvement name is required.",
        )

    def _modify_improvement(self) -> None:
        self._modify_record(
            self.improvements_table,
            HOUSE_IMPROVEMENT_ID_ROLE,
            HouseImprovementDialog,
            "Modify House Improvement",
            "improvement_data",
            "house_improvements",
            ("name", "priority", "estimated_cost", "notes"),
            "name",
            self._load_improvements,
            "Improvement name is required.",
        )

    def _remove_improvement(self) -> None:
        self._remove_record(
            self.improvements_table,
            HOUSE_IMPROVEMENT_ID_ROLE,
            "house_improvements",
            self._load_improvements,
        )

    def _add_record(
        self,
        dialog_class,
        title: str,
        data_method: str,
        table: str,
        columns: tuple[str, ...],
        required_key: str,
        reload_callback,
        warning: str,
    ) -> None:
        dialog = dialog_class(self, title)
        if dialog.exec() != QDialog.Accepted:
            return
        data = getattr(dialog, data_method)()
        if not self._validate_required(data, required_key, warning):
            return
        placeholders = ", ".join("?" for _ in columns)
        with self.database.connect() as connection:
            connection.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(data[column] for column in columns),
            )
        reload_callback()

    def _modify_record(
        self,
        table_widget: QTableWidget,
        role: int,
        dialog_class,
        title: str,
        data_method: str,
        table: str,
        columns: tuple[str, ...],
        required_key: str,
        reload_callback,
        warning: str,
    ) -> None:
        record_id = self._selected_row_id(table_widget, role)
        if record_id is None:
            return
        with self.database.connect() as connection:
            row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            return
        dialog = dialog_class(self, title, dict(row))
        if dialog.exec() != QDialog.Accepted:
            return
        data = getattr(dialog, data_method)()
        if not self._validate_required(data, required_key, warning):
            return
        assignments = ", ".join(f"{column} = ?" for column in columns)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE {table} SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*[data[column] for column in columns], record_id),
            )
        reload_callback()

    def _remove_record(
        self,
        table_widget: QTableWidget,
        role: int,
        table: str,
        reload_callback,
    ) -> None:
        record_id = self._selected_row_id(table_widget, role)
        if record_id is None:
            return
        with self.database.connect() as connection:
            connection.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        reload_callback()

    def _rows(self, query: str):
        with self.database.connect() as connection:
            return connection.execute(query).fetchall()

    def _set_row(
        self,
        table: QTableWidget,
        row_index: int,
        values: tuple[object, ...],
        role: int,
        record_id: int,
    ) -> None:
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value or ""))
            if column == 0:
                item.setData(role, record_id)
            table.setItem(row_index, column, item)

    def _selected_row_id(self, table: QTableWidget, role: int) -> int | None:
        row = table.currentRow()
        item = table.item(row, 0) if row >= 0 else None
        return item.data(role) if item else None

    def _validate_required(self, data: dict[str, object], key: str, warning: str) -> bool:
        if not data[key]:
            QMessageBox.warning(self, "Missing Required Field", warning)
            return False
        return True

    def _action_row(self, add_callback, modify_callback, remove_callback) -> QHBoxLayout:
        row = QHBoxLayout()
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(add_callback)
        modify_button.clicked.connect(modify_callback)
        remove_button.clicked.connect(remove_callback)
        row.addStretch()
        row.addWidget(add_button)
        row.addWidget(modify_button)
        row.addWidget(remove_button)
        return row

    def _panel(self, name: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName(name)
        panel.setStyleSheet(
            f"""
            QFrame#{name} {{
                background: #231C20;
                border: 1px solid #665451;
                border-radius: 8px;
            }}
            """
        )
        return panel

    def _configure_table(self, table: QTableWidget) -> None:
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

    def _money(self, value: object) -> str:
        return f"${float(value or 0):,.2f}"

    def _preview(self, value: object) -> str:
        collapsed = " ".join(str(value or "").split())
        return collapsed[:80] + "..." if len(collapsed) > 80 else collapsed
