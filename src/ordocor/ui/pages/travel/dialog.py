from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


TRAVEL_ID_ROLE = Qt.UserRole + 1


class TravelDestinationDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        destination: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(540, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.country_input = QLineEdit(str(destination.get("country", "")) if destination else "")
        self.country_input.setPlaceholderText("Country")

        self.city_input = QLineEdit(str(destination.get("city", "")) if destination else "")
        self.city_input.setPlaceholderText("City")

        self.priority_input = QComboBox()
        self.priority_input.addItems(("High", "Medium", "Low"))
        if destination and destination.get("priority"):
            index = self.priority_input.findText(str(destination["priority"]).title())
            if index >= 0:
                self.priority_input.setCurrentIndex(index)

        self.season_input = QLineEdit(
            str(destination.get("target_season", "")) if destination else ""
        )
        self.season_input.setPlaceholderText("Example: Spring, Summer, Winter")

        self.year_input = QLineEdit(
            str(destination.get("target_year", "") or "") if destination else ""
        )
        self.year_input.setValidator(QIntValidator(0, 9999, self.year_input))
        self.year_input.setPlaceholderText("Example: 2027")

        self.notes_input = QTextEdit(str(destination.get("notes", "")) if destination else "")
        self.notes_input.setPlaceholderText(
            "Why you want to go, ideas, budget notes, must-see places."
        )

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Country"), 0, 0)
        form.addWidget(self.country_input, 0, 1)
        form.addWidget(QLabel("City"), 1, 0)
        form.addWidget(self.city_input, 1, 1)
        form.addWidget(QLabel("Priority"), 2, 0)
        form.addWidget(self.priority_input, 2, 1)
        form.addWidget(QLabel("Target Season"), 3, 0)
        form.addWidget(self.season_input, 3, 1)
        form.addWidget(QLabel("Target Year"), 4, 0)
        form.addWidget(self.year_input, 4, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(QLabel("Notes"))
        layout.addWidget(self.notes_input, stretch=1)
        layout.addWidget(buttons)

    def destination_data(self) -> dict[str, object]:
        return {
            "country": self.country_input.text().strip(),
            "city": self.city_input.text().strip(),
            "priority": self.priority_input.currentText(),
            "target_season": self.season_input.text().strip(),
            "target_year": int(self.year_input.text()) if self.year_input.text().strip() else None,
            "notes": self.notes_input.toPlainText().strip(),
        }
