from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


PROJECT_ID_ROLE = Qt.UserRole + 1


class ProjectDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        project: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.name_input = QLineEdit(str(project.get("name", "")) if project else "")
        self.name_input.setPlaceholderText("Project name")

        self.description_input = QTextEdit(str(project.get("description", "")) if project else "")
        self.description_input.setPlaceholderText("Write what this project is, goals, and notes.")

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Project Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.description_input, stretch=1)
        layout.addWidget(buttons)

    def project_data(self) -> dict[str, str]:
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
        }
