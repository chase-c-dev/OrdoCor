from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.ui.pages.recipes import page as recipes_module
from ordocor.ui.pages.recipes.page import RecipesPage
from ordocor.ui.pages.recipes.repository import RecipeRepository


RECIPE = {
    "name": "Soup",
    "category": "Dinner",
    "servings": 4,
    "prep_minutes": 10,
    "cook_minutes": 30,
    "ingredients": "Water",
    "instructions": "Cook",
    "notes": "Warm",
}


def test_recipe_repository_crud(database):
    repository = RecipeRepository(database)
    repository.add_category("Dinner")
    repository.add_category("Dinner")
    assert repository.categories() == ["Dinner"]

    recipe_id = repository.add(RECIPE)
    assert repository.get(recipe_id)["name"] == "Soup"
    assert len(repository.list_recipes("All", "")) == 1
    assert len(repository.list_recipes("Dinner", "Sou")) == 1
    assert repository.list_recipes("Dessert", "") == []

    updated = dict(RECIPE, name="Stew")
    repository.update(recipe_id, updated)
    assert repository.get(recipe_id)["name"] == "Stew"

    repository.set_image(recipe_id, b"image", "image.png")
    assert repository.get(recipe_id)["image_name"] == "image.png"
    repository.delete(recipe_id)
    assert repository.get(recipe_id) is None


def test_recipe_page_workflow(qapp, database, monkeypatch, tmp_path):
    page = RecipesPage(database)
    assert page.category_filter.minimumWidth() >= 180
    assert page.category_filter.minimumContentsLength() >= 18
    page._change_page(1)
    page._remove_recipe()
    page._select_image()
    accepted = SimpleNamespace(exec=lambda: QDialog.Accepted, recipe_data=lambda: RECIPE)
    monkeypatch.setattr(recipes_module, "RecipeDialog", lambda *args: accepted)
    page._add_recipe()
    assert page.recipe_title.text() == "Soup"

    page._change_page(-1)
    page._change_page(1)
    recipe_id = page._current_recipe_id()
    assert recipe_id is not None
    assert page._recipe_by_id(recipe_id)["name"] == "Soup"
    assert page._recipe_categories() == ["Dinner"]

    page._modify_recipe()
    assert (
        page._recipe_meta(page.recipes[0]) == "Dinner  |  Serves 4  |  Prep 10 min  |  Cook 30 min"
    )
    assert "INGREDIENTS" in page._recipe_body(page.recipes[0])

    monkeypatch.setattr(
        recipes_module.QInputDialog,
        "getText",
        lambda *args: ("Dessert", True),
    )
    page._add_category()
    assert "Dessert" in page._recipe_categories()
    monkeypatch.setattr(recipes_module.QInputDialog, "getText", lambda *args: ("", False))
    page._add_category()

    image_path = tmp_path / "image.png"
    image = QImage(2, 2, QImage.Format_RGB32)
    image.fill(0xFFFFFF)
    image.save(str(image_path))
    monkeypatch.setattr(
        recipes_module.QFileDialog,
        "getOpenFileName",
        lambda *args: (str(image_path), "Images"),
    )
    page._select_image()
    assert page.recipes[0]["image_name"] == "image.png"

    monkeypatch.setattr(
        recipes_module.QFileDialog,
        "getOpenFileName",
        lambda *args: ("", ""),
    )
    page._select_image()

    page._render_image(b"not an image")

    page._remove_recipe()
    assert page._current_recipe_id() is None
    assert page.recipe_title.text() == "No recipes found"

    rejected = SimpleNamespace(exec=lambda: QDialog.Rejected, recipe_data=lambda: RECIPE)
    monkeypatch.setattr(recipes_module, "RecipeDialog", lambda *args: rejected)
    page._add_recipe()
    page._modify_recipe()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    assert page._validate_recipe(dict(RECIPE, name="")) is False
    assert page._recipe_body({}) == "No recipe details have been added yet."
    page._clear_image()


def test_recipe_invalid_and_missing_edit_paths(qapp, database, monkeypatch):
    page = RecipesPage(database)
    recipe_id = page.repository.add(RECIPE)
    page._load_recipes()

    rejected = SimpleNamespace(exec=lambda: QDialog.Rejected, recipe_data=lambda: RECIPE)
    monkeypatch.setattr(recipes_module, "RecipeDialog", lambda *args: rejected)
    page._modify_recipe()

    invalid = dict(RECIPE, name="")
    accepted_invalid = SimpleNamespace(
        exec=lambda: QDialog.Accepted,
        recipe_data=lambda: invalid,
    )
    monkeypatch.setattr(recipes_module, "RecipeDialog", lambda *args: accepted_invalid)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    page._modify_recipe()
    page._add_recipe()

    monkeypatch.setattr(page, "_recipe_by_id", lambda recipe_id: None)
    page._modify_recipe()
    page._show_recipe(recipe_id + 100)
