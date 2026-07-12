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
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database
from ordocor.ui.pages.property_dialogs import FieldSpec, PropertyFormDialog


VEHICLE_ID_ROLE = Qt.UserRole + 1
VEHICLE_MAINTENANCE_ID_ROLE = Qt.UserRole + 2
VEHICLE_WISHLIST_ID_ROLE = Qt.UserRole + 3

VEHICLE_FIELDS = (
    FieldSpec("name", "Vehicle Name"),
    FieldSpec("make", "Make"),
    FieldSpec("model", "Model"),
    FieldSpec("vehicle_year", "Year", "integer_text"),
    FieldSpec("vin", "VIN"),
    FieldSpec("notes", "Notes", "multiline"),
)
MAINTENANCE_FIELDS = (
    FieldSpec("title", "Maintenance Item"),
    FieldSpec("due_date", "Due Date", "date"),
    FieldSpec("video_url", "YouTube or Reference Link"),
    FieldSpec("notes", "Notes", "multiline"),
)
WISHLIST_FIELDS = (
    FieldSpec("item_name", "Item"),
    FieldSpec("category", "Category"),
    FieldSpec("estimated_price", "Estimated Price", "money"),
    FieldSpec("notes", "Notes", "multiline"),
)


class VehicleDialog(PropertyFormDialog):
    def __init__(
        self, parent: QWidget | None, title: str, vehicle: dict[str, object] | None = None
    ):
        super().__init__(parent, title, VEHICLE_FIELDS, vehicle)

    def vehicle_data(self) -> dict[str, object]:
        return self.form_data()


class VehicleMaintenanceDialog(PropertyFormDialog):
    def __init__(self, parent: QWidget | None, title: str, item: dict[str, object] | None = None):
        super().__init__(parent, title, MAINTENANCE_FIELDS, item)

    def maintenance_data(self) -> dict[str, object]:
        return self.form_data()


class VehicleWishlistDialog(PropertyFormDialog):
    def __init__(self, parent: QWidget | None, title: str, item: dict[str, object] | None = None):
        super().__init__(parent, title, WISHLIST_FIELDS, item)

    def wishlist_data(self) -> dict[str, object]:
        return self.form_data()


class VehiclePage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self._load_vehicles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Vehicle")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        splitter = QSplitter()
        splitter.addWidget(self._vehicle_panel())
        splitter.addWidget(self._details_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(heading)
        layout.addWidget(splitter, stretch=1)

    def _vehicle_panel(self) -> QFrame:
        panel = self._panel("vehiclePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Vehicles")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_vehicle)
        modify_button.clicked.connect(self._modify_vehicle)
        remove_button.clicked.connect(self._remove_vehicle)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.vehicle_table = QTableWidget(0, 3)
        self.vehicle_table.setHorizontalHeaderLabels(("Vehicle", "Make", "Model"))
        self.vehicle_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.vehicle_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vehicle_table.verticalHeader().setVisible(False)
        self.vehicle_table.currentCellChanged.connect(lambda *_args: self._load_vehicle_details())
        self.vehicle_table.doubleClicked.connect(self._modify_vehicle)

        layout.addLayout(header)
        layout.addWidget(self.vehicle_table, stretch=1)
        return panel

    def _details_panel(self) -> QFrame:
        panel = self._panel("vehicleDetailsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.vehicle_context_label = QLabel("Select a vehicle to manage related items.")
        self.vehicle_context_label.setStyleSheet("color: #B6A896; font-size: 12px;")
        self.vehicle_tabs = QTabWidget()
        self.vehicle_tabs.addTab(self._maintenance_tab(), "Maintenance")
        self.vehicle_tabs.addTab(self._wishlist_tab(), "Wishlist")

        layout.addWidget(self.vehicle_context_label)
        layout.addWidget(self.vehicle_tabs, stretch=1)
        return panel

    def _maintenance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QHBoxLayout()
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        open_button = QPushButton("Open Video")
        add_button.clicked.connect(self._add_maintenance)
        modify_button.clicked.connect(self._modify_maintenance)
        remove_button.clicked.connect(self._remove_maintenance)
        open_button.clicked.connect(self._open_maintenance_link)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)
        header.addWidget(open_button)

        self.maintenance_table = QTableWidget(0, 4)
        self.maintenance_table.setHorizontalHeaderLabels(("Item", "Due Date", "Link", "Notes"))
        self._configure_table(self.maintenance_table)
        self.maintenance_table.doubleClicked.connect(self._modify_maintenance)

        layout.addLayout(header)
        layout.addWidget(self.maintenance_table, stretch=1)
        return page

    def _wishlist_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QHBoxLayout()
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_wishlist_item)
        modify_button.clicked.connect(self._modify_wishlist_item)
        remove_button.clicked.connect(self._remove_wishlist_item)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.vehicle_wishlist_table = QTableWidget(0, 4)
        self.vehicle_wishlist_table.setHorizontalHeaderLabels(
            ("Item", "Category", "Price", "Notes")
        )
        self._configure_table(self.vehicle_wishlist_table)
        self.vehicle_wishlist_table.doubleClicked.connect(self._modify_wishlist_item)

        layout.addLayout(header)
        layout.addWidget(self.vehicle_wishlist_table, stretch=1)
        return page

    def _load_vehicles(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, make, model FROM vehicles ORDER BY name, id"
            ).fetchall()
        self.vehicle_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.vehicle_table.insertRow(row_index)
            for column, value in enumerate((row["name"], row["make"], row["model"])):
                item = QTableWidgetItem(str(value or ""))
                if column == 0:
                    item.setData(VEHICLE_ID_ROLE, row["id"])
                self.vehicle_table.setItem(row_index, column, item)
        if rows and self.vehicle_table.currentRow() < 0:
            self.vehicle_table.selectRow(0)
        self._load_vehicle_details()

    def _load_vehicle_details(self) -> None:
        vehicle_id = self._selected_vehicle_id()
        self.vehicle_context_label.setText(
            "Select a vehicle to manage related items."
            if vehicle_id is None
            else "Maintenance and wishlist items are saved to the selected vehicle."
        )
        self._load_maintenance()
        self._load_wishlist()

    def _add_vehicle(self) -> None:
        dialog = VehicleDialog(self, "Add Vehicle")
        if dialog.exec() != QDialog.Accepted:
            return
        vehicle = dialog.vehicle_data()
        if not self._validate_required(
            vehicle, "name", "Missing Vehicle Name", "Vehicle name is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO vehicles (name, make, model, vehicle_year, vin, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    vehicle["name"],
                    vehicle["make"],
                    vehicle["model"],
                    vehicle["vehicle_year"],
                    vehicle["vin"],
                    vehicle["notes"],
                ),
            )
        self._load_vehicles()

    def _modify_vehicle(self) -> None:
        vehicle_id = self._selected_vehicle_id()
        if vehicle_id is None:
            return
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
            ).fetchone()
        if row is None:
            return
        dialog = VehicleDialog(self, "Modify Vehicle", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return
        vehicle = dialog.vehicle_data()
        if not self._validate_required(
            vehicle, "name", "Missing Vehicle Name", "Vehicle name is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE vehicles
                SET name = ?, make = ?, model = ?, vehicle_year = ?, vin = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    vehicle["name"],
                    vehicle["make"],
                    vehicle["model"],
                    vehicle["vehicle_year"],
                    vehicle["vin"],
                    vehicle["notes"],
                    vehicle_id,
                ),
            )
        self._load_vehicles()

    def _remove_vehicle(self) -> None:
        vehicle_id = self._selected_vehicle_id()
        if vehicle_id is None:
            return
        with self.database.connect() as connection:
            connection.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        self._load_vehicles()

    def _load_maintenance(self) -> None:
        vehicle_id = self._selected_vehicle_id()
        self.maintenance_table.setRowCount(0)
        if vehicle_id is None:
            return
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, due_date, video_url, notes
                FROM vehicle_maintenance
                WHERE vehicle_id = ?
                ORDER BY due_date, title, id
                """,
                (vehicle_id,),
            ).fetchall()
        for row_index, row in enumerate(rows):
            self.maintenance_table.insertRow(row_index)
            values = (row["title"], row["due_date"], row["video_url"], self._preview(row["notes"]))
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                if column == 0:
                    item.setData(VEHICLE_MAINTENANCE_ID_ROLE, row["id"])
                self.maintenance_table.setItem(row_index, column, item)

    def _add_maintenance(self) -> None:
        vehicle_id = self._require_vehicle()
        if vehicle_id is None:
            return
        dialog = VehicleMaintenanceDialog(self, "Add Vehicle Maintenance")
        if dialog.exec() != QDialog.Accepted:
            return
        item = dialog.maintenance_data()
        if not self._validate_required(
            item, "title", "Missing Maintenance Item", "Maintenance item is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO vehicle_maintenance (vehicle_id, title, due_date, video_url, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (vehicle_id, item["title"], item["due_date"], item["video_url"], item["notes"]),
            )
        self._load_maintenance()

    def _modify_maintenance(self) -> None:
        item_id = self._selected_row_id(self.maintenance_table, VEHICLE_MAINTENANCE_ID_ROLE)
        if item_id is None:
            return
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, title, due_date, video_url, notes FROM vehicle_maintenance WHERE id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return
        dialog = VehicleMaintenanceDialog(self, "Modify Vehicle Maintenance", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return
        item = dialog.maintenance_data()
        if not self._validate_required(
            item, "title", "Missing Maintenance Item", "Maintenance item is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE vehicle_maintenance
                SET title = ?, due_date = ?, video_url = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (item["title"], item["due_date"], item["video_url"], item["notes"], item_id),
            )
        self._load_maintenance()

    def _remove_maintenance(self) -> None:
        item_id = self._selected_row_id(self.maintenance_table, VEHICLE_MAINTENANCE_ID_ROLE)
        if item_id is None:
            return
        with self.database.connect() as connection:
            connection.execute("DELETE FROM vehicle_maintenance WHERE id = ?", (item_id,))
        self._load_maintenance()

    def _open_maintenance_link(self) -> None:
        row = self.maintenance_table.currentRow()
        item = self.maintenance_table.item(row, 2) if row >= 0 else None
        url = item.text().strip() if item else ""
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _load_wishlist(self) -> None:
        vehicle_id = self._selected_vehicle_id()
        self.vehicle_wishlist_table.setRowCount(0)
        if vehicle_id is None:
            return
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, item_name, category, estimated_price, notes
                FROM vehicle_wishlist
                WHERE vehicle_id = ?
                ORDER BY category, item_name, id
                """,
                (vehicle_id,),
            ).fetchall()
        for row_index, row in enumerate(rows):
            self.vehicle_wishlist_table.insertRow(row_index)
            values = (
                row["item_name"],
                row["category"],
                self._money(row["estimated_price"]),
                self._preview(row["notes"]),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                if column == 0:
                    item.setData(VEHICLE_WISHLIST_ID_ROLE, row["id"])
                self.vehicle_wishlist_table.setItem(row_index, column, item)

    def _add_wishlist_item(self) -> None:
        vehicle_id = self._require_vehicle()
        if vehicle_id is None:
            return
        dialog = VehicleWishlistDialog(self, "Add Vehicle Wishlist Item")
        if dialog.exec() != QDialog.Accepted:
            return
        item = dialog.wishlist_data()
        if not self._validate_required(
            item, "item_name", "Missing Wishlist Item", "Wishlist item is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO vehicle_wishlist (vehicle_id, item_name, category, estimated_price, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    vehicle_id,
                    item["item_name"],
                    item["category"],
                    item["estimated_price"],
                    item["notes"],
                ),
            )
        self._load_wishlist()

    def _modify_wishlist_item(self) -> None:
        item_id = self._selected_row_id(self.vehicle_wishlist_table, VEHICLE_WISHLIST_ID_ROLE)
        if item_id is None:
            return
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, item_name, category, estimated_price, notes FROM vehicle_wishlist WHERE id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return
        dialog = VehicleWishlistDialog(self, "Modify Vehicle Wishlist Item", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return
        item = dialog.wishlist_data()
        if not self._validate_required(
            item, "item_name", "Missing Wishlist Item", "Wishlist item is required."
        ):
            return
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE vehicle_wishlist
                SET item_name = ?, category = ?, estimated_price = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    item["item_name"],
                    item["category"],
                    item["estimated_price"],
                    item["notes"],
                    item_id,
                ),
            )
        self._load_wishlist()

    def _remove_wishlist_item(self) -> None:
        item_id = self._selected_row_id(self.vehicle_wishlist_table, VEHICLE_WISHLIST_ID_ROLE)
        if item_id is None:
            return
        with self.database.connect() as connection:
            connection.execute("DELETE FROM vehicle_wishlist WHERE id = ?", (item_id,))
        self._load_wishlist()

    def _selected_vehicle_id(self) -> int | None:
        return self._selected_row_id(self.vehicle_table, VEHICLE_ID_ROLE)

    def _selected_row_id(self, table: QTableWidget, role: int) -> int | None:
        row = table.currentRow()
        item = table.item(row, 0) if row >= 0 else None
        return item.data(role) if item else None

    def _require_vehicle(self) -> int | None:
        vehicle_id = self._selected_vehicle_id()
        if vehicle_id is None:
            QMessageBox.warning(self, "Select Vehicle", "Select a vehicle first.")
        return vehicle_id

    def _validate_required(
        self,
        data: dict[str, object],
        key: str,
        title: str,
        message: str,
    ) -> bool:
        if not data[key]:
            QMessageBox.warning(self, title, message)
            return False
        return True

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
