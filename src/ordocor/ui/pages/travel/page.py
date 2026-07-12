from __future__ import annotations

from PySide6.QtCore import Qt
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
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database

from .dialog import TravelDestinationDialog


TRAVEL_ID_ROLE = Qt.UserRole + 1


class TravelPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self._load_destinations()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Travel")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        panel = QFrame()
        panel.setObjectName("travelPanel")
        panel.setStyleSheet(
            """
            QFrame#travelPanel {
                background: #231C20;
                border: 1px solid #665451;
                border-radius: 8px;
            }
            """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Places to Visit")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_destination)
        modify_button.clicked.connect(self._modify_destination)
        remove_button.clicked.connect(self._remove_destination)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.travel_table = QTableWidget(0, 5)
        self.travel_table.setHorizontalHeaderLabels(
            ("Country", "City", "Priority", "Target Season", "Target Year")
        )
        self.travel_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.travel_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.travel_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.travel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.travel_table.verticalHeader().setVisible(False)
        self.travel_table.doubleClicked.connect(self._modify_destination)

        hint = QLabel("Double-click a destination to edit notes and travel ideas.")
        hint.setStyleSheet("color: #B6A896; font-size: 12px;")

        panel_layout.addLayout(header)
        panel_layout.addWidget(hint)
        panel_layout.addWidget(self.travel_table, stretch=1)

        layout.addWidget(heading)
        layout.addWidget(panel, stretch=1)

    def _load_destinations(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, country, city, priority, target_season, target_year
                FROM travel_destinations
                ORDER BY country, city, id
                """
            ).fetchall()

        self.travel_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.travel_table.insertRow(row_index)
            values = (
                row["country"] or "",
                row["city"] or "",
                row["priority"] or "",
                row["target_season"] or "",
                str(row["target_year"] or ""),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(TRAVEL_ID_ROLE, row["id"])
                self.travel_table.setItem(row_index, column, item)

    def _add_destination(self) -> None:
        dialog = TravelDestinationDialog(self, "Add Travel Destination")
        if dialog.exec() != QDialog.Accepted:
            return

        destination = dialog.destination_data()
        if not self._validate_destination(destination):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO travel_destinations (
                    country, city, priority, target_season, target_year, notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    destination["country"],
                    destination["city"],
                    destination["priority"],
                    destination["target_season"],
                    destination["target_year"],
                    destination["notes"],
                ),
            )
        self._load_destinations()

    def _modify_destination(self) -> None:
        destination_id = self._selected_destination_id()
        if destination_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, country, city, priority, target_season, target_year, notes
                FROM travel_destinations
                WHERE id = ?
                """,
                (destination_id,),
            ).fetchone()

        if row is None:
            return

        dialog = TravelDestinationDialog(self, "Modify Travel Destination", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        destination = dialog.destination_data()
        if not self._validate_destination(destination):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE travel_destinations
                SET country = ?,
                    city = ?,
                    priority = ?,
                    target_season = ?,
                    target_year = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    destination["country"],
                    destination["city"],
                    destination["priority"],
                    destination["target_season"],
                    destination["target_year"],
                    destination["notes"],
                    destination_id,
                ),
            )
        self._load_destinations()

    def _remove_destination(self) -> None:
        destination_id = self._selected_destination_id()
        if destination_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM travel_destinations WHERE id = ?", (destination_id,))
        self._load_destinations()

    def _selected_destination_id(self) -> int | None:
        selected_items = self.travel_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.travel_table.item(row, 0)
        return item.data(TRAVEL_ID_ROLE) if item else None

    def _validate_destination(self, destination: dict[str, object]) -> bool:
        if not destination["country"] and not destination["city"]:
            QMessageBox.warning(
                self,
                "Missing Destination",
                "Enter at least a country or city.",
            )
            return False
        return True
