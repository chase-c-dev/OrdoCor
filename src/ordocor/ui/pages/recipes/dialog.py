from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class RecipeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        categories: list[str],
        recipe: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(680, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.name_input = QLineEdit(str(recipe.get("name", "")) if recipe else "")
        self.name_input.setPlaceholderText("Example: Sunday Red Sauce")

        self.category_input = QComboBox()
        self.category_input.addItem("")
        self.category_input.addItems(categories)
        if recipe and recipe.get("category"):
            index = self.category_input.findText(str(recipe["category"]))
            if index >= 0:
                self.category_input.setCurrentIndex(index)

        self.servings_input = QSpinBox()
        self.servings_input.setRange(0, 500)
        self.servings_input.setValue(int(recipe.get("servings", 0) or 0) if recipe else 0)

        self.prep_time_input = QSpinBox()
        self.prep_time_input.setRange(0, 3000)
        self.prep_time_input.setSuffix(" min")
        self.prep_time_input.setValue(int(recipe.get("prep_minutes", 0) or 0) if recipe else 0)

        self.cook_time_input = QSpinBox()
        self.cook_time_input.setRange(0, 3000)
        self.cook_time_input.setSuffix(" min")
        self.cook_time_input.setValue(int(recipe.get("cook_minutes", 0) or 0) if recipe else 0)

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Recipe Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1, 1, 3)
        form.addWidget(QLabel("Category"), 1, 0)
        form.addWidget(self.category_input, 1, 1, 1, 3)
        form.addWidget(QLabel("Servings"), 2, 0)
        form.addWidget(self.servings_input, 2, 1)
        form.addWidget(QLabel("Prep Time"), 2, 2)
        form.addWidget(self.prep_time_input, 2, 3)
        form.addWidget(QLabel("Cook Time"), 3, 0)
        form.addWidget(self.cook_time_input, 3, 1)

        self.ingredients_input = QTextEdit(str(recipe.get("ingredients", "")) if recipe else "")
        self.ingredients_input.setPlaceholderText("Add one ingredient per line")

        self.instructions_input = QTextEdit(str(recipe.get("instructions", "")) if recipe else "")
        self.instructions_input.setPlaceholderText("Write the recipe steps here")

        self.notes_input = QTextEdit(str(recipe.get("notes", "")) if recipe else "")
        self.notes_input.setPlaceholderText("Optional notes, substitutions, or serving ideas")
        self.notes_input.setFixedHeight(100)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self._section_label("Ingredients"))
        layout.addWidget(self.ingredients_input, stretch=1)
        layout.addWidget(self._section_label("Instructions"))
        layout.addWidget(self.instructions_input, stretch=2)
        layout.addWidget(self._section_label("Notes"))
        layout.addWidget(self.notes_input)
        layout.addWidget(buttons)

    def recipe_data(self) -> dict[str, object]:
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_input.currentText().strip(),
            "servings": self.servings_input.value(),
            "prep_minutes": self.prep_time_input.value(),
            "cook_minutes": self.cook_time_input.value(),
            "ingredients": self.ingredients_input.toPlainText().strip(),
            "instructions": self.instructions_input.toPlainText().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #F3E7C9; font-size: 14px; font-weight: 800;")
        return label
