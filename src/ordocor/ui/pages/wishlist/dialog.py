from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


WISHLIST_ID_ROLE = Qt.UserRole + 1


class WishlistItemDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        item: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(520, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.name_input = QLineEdit(str(item.get("name", "")) if item else "")
        self.name_input.setPlaceholderText("Product name")

        self.category_input = QLineEdit(str(item.get("category", "")) if item else "")
        self.category_input.setPlaceholderText("Example: Tech, Home, Clothing")

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1_000_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        self.price_input.setValue(float(item.get("estimated_price", 0) or 0) if item else 0)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1_000_000)
        self.quantity_input.setValue(int(item.get("quantity", 1) or 1) if item else 1)

        self.notes_input = QTextEdit(str(item.get("notes", "")) if item else "")
        self.notes_input.setPlaceholderText("Optional notes, links, sizes, model numbers, etc.")

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Product"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Category"), 1, 0)
        form.addWidget(self.category_input, 1, 1)
        form.addWidget(QLabel("Estimated Price"), 2, 0)
        form.addWidget(self.price_input, 2, 1)
        form.addWidget(QLabel("Quantity"), 3, 0)
        form.addWidget(self.quantity_input, 3, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(QLabel("Notes"))
        layout.addWidget(self.notes_input, stretch=1)
        layout.addWidget(buttons)

    def wishlist_data(self) -> dict[str, object]:
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_input.text().strip(),
            "estimated_price": self.price_input.value(),
            "quantity": self.quantity_input.value(),
            "notes": self.notes_input.toPlainText().strip(),
        }
