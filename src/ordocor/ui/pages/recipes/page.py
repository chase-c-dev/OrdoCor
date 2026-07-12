from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database

from .dialog import RecipeDialog
from .repository import RecipeRepository


class RecipesPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.repository = RecipeRepository(database)
        self.recipes: list[dict[str, object]] = []
        self.current_index = 0
        self._build_ui()
        self._refresh_categories()
        self._load_recipes()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Recipes")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        filters = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(180)
        self.category_filter.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.category_filter.setMinimumContentsLength(18)
        self.category_filter.currentTextChanged.connect(self._load_recipes)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recipes by name")
        self.search_input.textChanged.connect(self._load_recipes)

        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_category_button = QPushButton("Add Category")
        add_button.clicked.connect(self._add_recipe)
        modify_button.clicked.connect(self._modify_recipe)
        remove_button.clicked.connect(self._remove_recipe)
        add_category_button.clicked.connect(self._add_category)

        filters.addWidget(QLabel("Category"))
        filters.addWidget(self.category_filter)
        filters.addWidget(self.search_input, stretch=1)
        filters.addWidget(add_button)
        filters.addWidget(modify_button)
        filters.addWidget(remove_button)
        filters.addWidget(add_category_button)

        self.book = QFrame()
        self.book.setObjectName("recipeBook")
        self.book.setStyleSheet(
            """
            QFrame#recipeBook {
                background: #231C20;
                border: 1px solid #665451;
                border-radius: 8px;
            }
            """
        )
        book_layout = QVBoxLayout(self.book)
        book_layout.setContentsMargins(22, 22, 22, 22)
        book_layout.setSpacing(16)

        top = QHBoxLayout()
        self.previous_button = QPushButton("< Previous")
        self.next_button = QPushButton("Next >")
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("color: #B6A896; font-weight: 700;")
        self.previous_button.clicked.connect(lambda: self._change_page(-1))
        self.next_button.clicked.connect(lambda: self._change_page(1))
        top.addWidget(self.previous_button)
        top.addWidget(self.page_label, stretch=1)
        top.addWidget(self.next_button)

        page_content = QHBoxLayout()
        page_content.setSpacing(18)

        image_card = QFrame()
        image_card.setObjectName("recipeImageCard")
        image_card.setFixedWidth(360)
        image_card.setStyleSheet(
            """
            QFrame#recipeImageCard {
                background: #191518;
                border: 1px solid #665451;
                border-radius: 8px;
            }
            """
        )
        image_panel = QVBoxLayout(image_card)
        image_panel.setContentsMargins(16, 16, 16, 16)
        image_panel.setSpacing(12)

        image_title = QLabel("Image")
        image_title.setStyleSheet("color: #F3E7C9; font-size: 16px; font-weight: 800;")

        self.image_label = QLabel("Recipe Image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(328, 300)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background: #231C20;
                border: 1px dashed #76635E;
                border-radius: 8px;
                color: #9B8F83;
                font-size: 16px;
                font-weight: 800;
            }
            """
        )
        select_image_button = QPushButton("Select Image")
        select_image_button.clicked.connect(self._select_image)
        image_panel.addWidget(image_title)
        image_panel.addWidget(self.image_label)
        image_panel.addWidget(select_image_button)
        image_panel.addStretch()

        text_panel = QVBoxLayout()
        self.recipe_title = QLabel()
        self.recipe_title.setWordWrap(True)
        self.recipe_title.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        self.recipe_meta = QLabel()
        self.recipe_meta.setStyleSheet("color: #B6A896; font-size: 13px; font-weight: 700;")

        self.recipe_text = QTextEdit()
        self.recipe_text.setReadOnly(True)
        self.recipe_text.setMinimumHeight(360)

        text_panel.addWidget(self.recipe_title)
        text_panel.addWidget(self.recipe_meta)
        text_panel.addWidget(self.recipe_text, stretch=1)

        page_content.addWidget(image_card, alignment=Qt.AlignTop)
        page_content.addLayout(text_panel, stretch=1)

        book_layout.addLayout(top)
        book_layout.addLayout(page_content, stretch=1)

        layout.addWidget(heading)
        layout.addLayout(filters)
        layout.addWidget(self.book, stretch=1)

    def _refresh_categories(self) -> None:
        current = self.category_filter.currentText() if hasattr(self, "category_filter") else "All"
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("All")

        self.category_filter.addItems(self.repository.categories())

        index = self.category_filter.findText(current)
        self.category_filter.setCurrentIndex(index if index >= 0 else 0)
        self.category_filter.blockSignals(False)

    def _load_recipes(self) -> None:
        selected_category = self.category_filter.currentText()
        search = self.search_input.text().strip()

        self.recipes = self.repository.list_recipes(selected_category, search)
        self.current_index = min(self.current_index, max(len(self.recipes) - 1, 0))
        self._render_current_recipe()

    def _render_current_recipe(self) -> None:
        has_recipes = bool(self.recipes)
        self.previous_button.setEnabled(has_recipes and self.current_index > 0)
        self.next_button.setEnabled(has_recipes and self.current_index < len(self.recipes) - 1)

        if not has_recipes:
            self.page_label.setText("No recipes")
            self.recipe_title.setText("No recipes found")
            self.recipe_meta.setText("")
            self.recipe_text.setPlainText("Add a recipe to start building your cookbook.")
            self._clear_image()
            return

        recipe = self.recipes[self.current_index]
        self.page_label.setText(f"Recipe {self.current_index + 1} of {len(self.recipes)}")
        self.recipe_title.setText(str(recipe["name"] or "Untitled Recipe"))
        self.recipe_meta.setText(self._recipe_meta(recipe))
        self.recipe_text.setPlainText(self._recipe_body(recipe))
        self._render_image(recipe.get("image_data"))

    def _change_page(self, offset: int) -> None:
        if not self.recipes:
            return

        self.current_index = max(0, min(self.current_index + offset, len(self.recipes) - 1))
        self._render_current_recipe()

    def _add_recipe(self) -> None:
        dialog = RecipeDialog(self, "Add Recipe", self._recipe_categories())
        if dialog.exec() != QDialog.Accepted:
            return

        recipe = dialog.recipe_data()
        if not self._validate_recipe(recipe):
            return

        new_id = self.repository.add(recipe)

        self._refresh_categories()
        self._load_recipes()
        self._show_recipe(new_id)

    def _modify_recipe(self) -> None:
        recipe_id = self._current_recipe_id()
        if recipe_id is None:
            return

        recipe = self._recipe_by_id(recipe_id)
        if recipe is None:
            return

        dialog = RecipeDialog(self, "Modify Recipe", self._recipe_categories(), recipe)
        if dialog.exec() != QDialog.Accepted:
            return

        updated = dialog.recipe_data()
        if not self._validate_recipe(updated):
            return

        self.repository.update(recipe_id, updated)

        self._refresh_categories()
        self._load_recipes()
        self._show_recipe(recipe_id)

    def _add_category(self) -> None:
        category, accepted = QInputDialog.getText(self, "Add Recipe Category", "Category name")
        category = category.strip()
        if not accepted or not category:
            return

        self.repository.add_category(category)
        self._refresh_categories()

    def _remove_recipe(self) -> None:
        recipe_id = self._current_recipe_id()
        if recipe_id is None:
            return

        self.repository.delete(recipe_id)
        self.current_index = max(0, self.current_index - 1)
        self._refresh_categories()
        self._load_recipes()

    def _select_image(self) -> None:
        recipe_id = self._current_recipe_id()
        if recipe_id is None:
            return

        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Recipe Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not image_path:
            return

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        image_name = image_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        self.repository.set_image(recipe_id, image_data, image_name)

        self._load_recipes()
        self._show_recipe(recipe_id)

    def _show_recipe(self, recipe_id: int) -> None:
        for index, recipe in enumerate(self.recipes):
            if recipe["id"] == recipe_id:
                self.current_index = index
                self._render_current_recipe()
                return

    def _current_recipe_id(self) -> int | None:
        if not self.recipes:
            return None
        return int(self.recipes[self.current_index]["id"])

    def _recipe_by_id(self, recipe_id: int) -> dict[str, object] | None:
        return self.repository.get(recipe_id)

    def _recipe_categories(self) -> list[str]:
        return self.repository.categories()

    def _validate_recipe(self, recipe: dict[str, object]) -> bool:
        if not recipe["name"]:
            QMessageBox.warning(self, "Missing Recipe Name", "Recipe name is required.")
            return False
        return True

    def _recipe_meta(self, recipe: dict[str, object]) -> str:
        parts = []
        if recipe.get("category"):
            parts.append(str(recipe["category"]))
        if recipe.get("servings"):
            parts.append(f"Serves {recipe['servings']}")
        if recipe.get("prep_minutes"):
            parts.append(f"Prep {recipe['prep_minutes']} min")
        if recipe.get("cook_minutes"):
            parts.append(f"Cook {recipe['cook_minutes']} min")
        return "  |  ".join(parts)

    def _recipe_body(self, recipe: dict[str, object]) -> str:
        sections = []
        if recipe.get("ingredients"):
            sections.append(f"INGREDIENTS\n{recipe['ingredients']}")
        if recipe.get("instructions"):
            sections.append(f"INSTRUCTIONS\n{recipe['instructions']}")
        if recipe.get("notes"):
            sections.append(f"NOTES\n{recipe['notes']}")
        return "\n\n".join(sections) if sections else "No recipe details have been added yet."

    def _render_image(self, image_data: object) -> None:
        if not image_data:
            self._clear_image()
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(bytes(image_data)):
            self._clear_image()
            return

        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.image_label.setText("")

    def _clear_image(self) -> None:
        self.image_label.clear()
        self.image_label.setText("Recipe Image")
