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

from .dialog import WishlistItemDialog


WISHLIST_ID_ROLE = Qt.UserRole + 1


class WishlistPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self._load_items()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Wishlist")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        panel = QFrame()
        panel.setObjectName("wishlistPanel")
        panel.setStyleSheet(
            """
            QFrame#wishlistPanel {
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
        title = QLabel("Products to Purchase")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_item)
        modify_button.clicked.connect(self._modify_item)
        remove_button.clicked.connect(self._remove_item)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.wishlist_table = QTableWidget(0, 5)
        self.wishlist_table.setHorizontalHeaderLabels(
            ("Product", "Category", "Price", "Qty", "Total")
        )
        self.wishlist_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wishlist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.wishlist_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wishlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wishlist_table.verticalHeader().setVisible(False)
        self.wishlist_table.doubleClicked.connect(self._modify_item)

        hint = QLabel("Double-click a product to edit notes and details.")
        hint.setStyleSheet("color: #B6A896; font-size: 12px;")

        panel_layout.addLayout(header)
        panel_layout.addWidget(hint)
        panel_layout.addWidget(self.wishlist_table, stretch=1)

        layout.addWidget(heading)
        layout.addWidget(panel, stretch=1)

    def _load_items(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, category, estimated_price, quantity
                FROM wishlist_items
                ORDER BY category, name, id
                """
            ).fetchall()

        self.wishlist_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.wishlist_table.insertRow(row_index)
            total = float(row["estimated_price"] or 0) * int(row["quantity"] or 0)
            values = (
                row["name"] or "",
                row["category"] or "",
                self._money(row["estimated_price"]),
                str(row["quantity"] or ""),
                self._money(total),
            )
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                if column == 0:
                    table_item.setData(WISHLIST_ID_ROLE, row["id"])
                self.wishlist_table.setItem(row_index, column, table_item)

    def _add_item(self) -> None:
        dialog = WishlistItemDialog(self, "Add Wishlist Product")
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.wishlist_data()
        if not self._validate_item(item):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO wishlist_items (name, category, estimated_price, quantity, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item["name"],
                    item["category"],
                    item["estimated_price"],
                    item["quantity"],
                    item["notes"],
                ),
            )
        self._load_items()

    def _modify_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, category, estimated_price, quantity, notes
                FROM wishlist_items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()

        if row is None:
            return

        dialog = WishlistItemDialog(self, "Modify Wishlist Product", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        item = dialog.wishlist_data()
        if not self._validate_item(item):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE wishlist_items
                SET name = ?,
                    category = ?,
                    estimated_price = ?,
                    quantity = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    item["name"],
                    item["category"],
                    item["estimated_price"],
                    item["quantity"],
                    item["notes"],
                    item_id,
                ),
            )
        self._load_items()

    def _remove_item(self) -> None:
        item_id = self._selected_item_id()
        if item_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM wishlist_items WHERE id = ?", (item_id,))
        self._load_items()

    def _selected_item_id(self) -> int | None:
        selected_items = self.wishlist_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.wishlist_table.item(row, 0)
        return item.data(WISHLIST_ID_ROLE) if item else None

    def _validate_item(self, item: dict[str, object]) -> bool:
        if not item["name"]:
            QMessageBox.warning(self, "Missing Product Name", "Product name is required.")
            return False
        return True

    def _money(self, value: object) -> str:
        return f"${float(value or 0):,.2f}"
