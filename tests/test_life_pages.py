from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.ui.pages.projects import page as projects_module
from ordocor.ui.pages.projects.page import ProjectsPage
from ordocor.ui.pages.travel import page as travel_module
from ordocor.ui.pages.travel.page import TravelPage
from ordocor.ui.pages.wishlist import page as wishlist_module
from ordocor.ui.pages.wishlist.page import WishlistPage


CASES = [
    (
        projects_module,
        ProjectsPage,
        "ProjectDialog",
        "project_data",
        {"name": "OrdoCor", "description": "Build it"},
        "_add_project",
        "_modify_project",
        "_remove_project",
        "projects_table",
        "_validate_project",
        "projects",
    ),
    (
        wishlist_module,
        WishlistPage,
        "WishlistItemDialog",
        "wishlist_data",
        {
            "name": "Chair",
            "category": "Home",
            "estimated_price": 100,
            "quantity": 2,
            "notes": "Oak",
        },
        "_add_item",
        "_modify_item",
        "_remove_item",
        "wishlist_table",
        "_validate_item",
        "wishlist_items",
    ),
    (
        travel_module,
        TravelPage,
        "TravelDestinationDialog",
        "destination_data",
        {
            "country": "Japan",
            "city": "Tokyo",
            "priority": "High",
            "target_season": "Spring",
            "target_year": 2027,
            "notes": "Visit",
        },
        "_add_destination",
        "_modify_destination",
        "_remove_destination",
        "travel_table",
        "_validate_destination",
        "travel_destinations",
    ),
]


@pytest.mark.parametrize(
    (
        "module",
        "page_class",
        "dialog_name",
        "data_method",
        "data",
        "add_method",
        "modify_method",
        "remove_method",
        "table_name",
        "validate_method",
        "database_table",
    ),
    CASES,
)
def test_life_page_crud(
    qapp,
    database,
    monkeypatch,
    module,
    page_class,
    dialog_name,
    data_method,
    data,
    add_method,
    modify_method,
    remove_method,
    table_name,
    validate_method,
    database_table,
):
    page = page_class(database)
    table = getattr(page, table_name)

    accepted = SimpleNamespace(exec=lambda: QDialog.Accepted, **{data_method: lambda: data})
    monkeypatch.setattr(module, dialog_name, lambda *args: accepted)
    getattr(page, add_method)()
    assert table.rowCount() == 1

    table.selectRow(0)
    getattr(page, modify_method)()

    rejected = SimpleNamespace(exec=lambda: QDialog.Rejected, **{data_method: lambda: data})
    monkeypatch.setattr(module, dialog_name, lambda *args: rejected)
    table.selectRow(0)
    getattr(page, modify_method)()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    invalid = dict(data)
    if page_class is TravelPage:
        invalid["country"] = ""
        invalid["city"] = ""
    else:
        invalid["name"] = ""
    invalid_dialog = SimpleNamespace(
        exec=lambda: QDialog.Accepted,
        **{data_method: lambda: invalid},
    )
    monkeypatch.setattr(module, dialog_name, lambda *args: invalid_dialog)
    table.selectRow(0)
    getattr(page, modify_method)()

    with database.connect() as connection:
        connection.execute(f"DELETE FROM {database_table}")
    table.selectRow(0)
    getattr(page, modify_method)()

    table.selectRow(0)
    getattr(page, remove_method)()
    assert table.rowCount() == 0

    getattr(page, modify_method)()
    getattr(page, remove_method)()

    rejected = SimpleNamespace(exec=lambda: QDialog.Rejected, **{data_method: lambda: data})
    monkeypatch.setattr(module, dialog_name, lambda *args: rejected)
    getattr(page, add_method)()

    monkeypatch.setattr(module, dialog_name, lambda *args: invalid_dialog)
    getattr(page, add_method)()
    assert getattr(page, validate_method)(invalid) is False


def test_life_page_display_helpers(database):
    projects = ProjectsPage(database)
    assert projects._preview("a " * 100).endswith("...")
    assert projects._preview("short") == "short"

    wishlist = WishlistPage(database)
    assert wishlist._money(12.5) == "$12.50"
