from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


COLLECTIBLE_ID_ROLE = Qt.UserRole + 4


class CollectibleDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        collectible: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.name_input = QLineEdit(str(collectible.get("item_name", "")) if collectible else "")
        self.name_input.setPlaceholderText("Example: 1986 Fleer Michael Jordan")

        self.type_input = QLineEdit(str(collectible.get("category", "")) if collectible else "")
        self.type_input.setPlaceholderText("Example: Trading Card")

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1_000_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        self.price_input.setValue(
            float(collectible.get("target_price", 0) or 0) if collectible else 0
        )

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0, 1_000_000)
        self.quantity_input.setDecimals(0)
        self.quantity_input.setValue(
            float(collectible.get("quantity", 1) or 1) if collectible else 1
        )

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Item Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Type"), 1, 0)
        form.addWidget(self.type_input, 1, 1)
        form.addWidget(QLabel("Target Price"), 2, 0)
        form.addWidget(self.price_input, 2, 1)
        form.addWidget(QLabel("Quantity"), 3, 0)
        form.addWidget(self.quantity_input, 3, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def collectible_data(self) -> dict[str, object]:
        return {
            "item_name": self.name_input.text().strip(),
            "category": self.type_input.text().strip(),
            "target_price": self.price_input.value(),
            "quantity": int(self.quantity_input.value()),
        }


class CollectiblesMixin:
    def _collectibles_wishlist_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Collectibles")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_collectible)
        modify_button.clicked.connect(self._modify_collectible)
        remove_button.clicked.connect(self._remove_collectible)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.collectibles_table = QTableWidget(0, 4)
        self.collectibles_table.setHorizontalHeaderLabels(
            (
                "Item Name",
                "Type",
                "Target Price",
                "Quantity",
            )
        )
        self.collectibles_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.collectibles_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.collectibles_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.collectibles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.collectibles_table.verticalHeader().setVisible(False)
        self.collectibles_table.doubleClicked.connect(self._modify_collectible)

        layout.addLayout(header)
        layout.addWidget(self.collectibles_table, stretch=1)
        self._load_collectibles()
        return page

    def _load_collectibles(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, item_name, category, target_price, quantity
                    FROM investment_collectibles
                    ORDER BY category, item_name, id
                    """
            ).fetchall()

        self.collectibles_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.collectibles_table.insertRow(row_index)
            values = (
                row["item_name"] or "",
                row["category"] or "",
                self._money(row["target_price"]),
                str(row["quantity"] or 0),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(COLLECTIBLE_ID_ROLE, row["id"])
                self.collectibles_table.setItem(row_index, column, item)

    def _add_collectible(self) -> None:
        dialog = CollectibleDialog(self, "Add Wishlist Collectible")
        if dialog.exec() != QDialog.Accepted:
            return

        collectible = dialog.collectible_data()
        if not self._validate_collectible(collectible):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    INSERT INTO investment_collectibles (item_name, category, target_price, quantity)
                    VALUES (?, ?, ?, ?)
                    """,
                (
                    collectible["item_name"],
                    collectible["category"],
                    collectible["target_price"],
                    collectible["quantity"],
                ),
            )
        self._load_collectibles()

    def _modify_collectible(self) -> None:
        collectible_id = self._selected_collectible_id()
        if collectible_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT id, item_name, category, target_price, quantity
                    FROM investment_collectibles
                    WHERE id = ?
                    """,
                (collectible_id,),
            ).fetchone()

        if row is None:
            return

        dialog = CollectibleDialog(self, "Modify Wishlist Collectible", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        collectible = dialog.collectible_data()
        if not self._validate_collectible(collectible):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE investment_collectibles
                    SET item_name = ?,
                        category = ?,
                        target_price = ?,
                        quantity = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (
                    collectible["item_name"],
                    collectible["category"],
                    collectible["target_price"],
                    collectible["quantity"],
                    collectible_id,
                ),
            )
        self._load_collectibles()

    def _remove_collectible(self) -> None:
        collectible_id = self._selected_collectible_id()
        if collectible_id is None:
            return

        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM investment_collectibles WHERE id = ?", (collectible_id,)
            )
        self._load_collectibles()

    def _selected_collectible_id(self) -> int | None:
        selected_items = self.collectibles_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.collectibles_table.item(row, 0)
        return item.data(COLLECTIBLE_ID_ROLE) if item else None

    def _validate_collectible(self, collectible: dict[str, object]) -> bool:
        if not collectible["item_name"]:
            QMessageBox.warning(self, "Missing Collectible Details", "Item name is required.")
            return False
        return True
