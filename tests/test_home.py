from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.ui.pages.home import calendar_view, dialogs, todos
from ordocor.ui.pages.home.dialogs import CalendarDayDialog
from ordocor.ui.pages.home.models import CalendarItem, UPCOMING_DATE_ROLE
from ordocor.ui.pages.home.page import HomePage


def fake_text_dialog(title="Item", notes="Notes", result=QDialog.Accepted):
    return SimpleNamespace(
        exec=lambda: result,
        item=lambda: CalendarItem(id=None, title=title, notes=notes),
    )


def test_todo_workflow(qapp, database, monkeypatch):
    page = HomePage(database)
    monkeypatch.setattr(todos, "TextItemDialog", lambda *args: fake_text_dialog())
    page._add_todo()
    assert page.todo_list.count() == 1

    item = page.todo_list.item(0)
    item.setCheckState(Qt.Checked)
    assert page.todo_list.item(0).checkState() == Qt.Checked

    page.todo_list.setCurrentRow(0)
    monkeypatch.setattr(todos, "TextItemDialog", lambda *args: fake_text_dialog("Updated"))
    page._edit_todo()
    assert page.todo_list.item(0).text() == "Updated"

    page.todo_list.setCurrentRow(0)
    monkeypatch.setattr(
        todos,
        "TextItemDialog",
        lambda *args: fake_text_dialog(result=QDialog.Rejected),
    )
    page._edit_todo()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    page.todo_list.setCurrentRow(0)
    monkeypatch.setattr(todos, "TextItemDialog", lambda *args: fake_text_dialog(""))
    page._edit_todo()

    page.todo_list.setCurrentRow(0)
    with database.connect() as connection:
        connection.execute("DELETE FROM todo_items")
    page._edit_todo()

    page.todo_list.setCurrentRow(0)
    page._remove_todo()
    assert page.todo_list.count() == 0
    page._edit_todo()
    page._remove_todo()

    monkeypatch.setattr(
        todos,
        "TextItemDialog",
        lambda *args: fake_text_dialog(result=QDialog.Rejected),
    )
    page._add_todo()

    monkeypatch.setattr(todos, "TextItemDialog", lambda *args: fake_text_dialog(""))
    page._add_todo()

    page._loading_todos = True
    page._toggle_todo(SimpleNamespace())
    page._loading_todos = False


def test_calendar_day_dialog_crud(qapp, database, monkeypatch):
    selected = date.today()
    dialog = CalendarDayDialog(database, selected, None)
    monkeypatch.setattr(dialogs, "TextItemDialog", lambda *args: fake_text_dialog("Appointment"))
    dialog._add_item()
    assert dialog.items.count() == 1

    dialog.items.setCurrentRow(0)
    monkeypatch.setattr(dialogs, "TextItemDialog", lambda *args: fake_text_dialog("Updated"))
    dialog._edit_item()
    assert dialog.items.item(0).text() == "Updated"

    dialog.items.setCurrentRow(0)
    monkeypatch.setattr(
        dialogs,
        "TextItemDialog",
        lambda *args: fake_text_dialog(result=QDialog.Rejected),
    )
    dialog._edit_item()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)
    dialog.items.setCurrentRow(0)
    monkeypatch.setattr(dialogs, "TextItemDialog", lambda *args: fake_text_dialog(""))
    dialog._edit_item()

    dialog.items.setCurrentRow(0)
    with database.connect() as connection:
        connection.execute("DELETE FROM calendar_items")
    dialog._edit_item()

    dialog.items.setCurrentRow(0)
    dialog._remove_item()
    assert dialog.items.count() == 0
    dialog._edit_item()
    dialog._remove_item()

    monkeypatch.setattr(
        dialogs,
        "TextItemDialog",
        lambda *args: fake_text_dialog(result=QDialog.Rejected),
    )
    dialog._add_item()

    monkeypatch.setattr(dialogs, "TextItemDialog", lambda *args: fake_text_dialog(""))
    dialog._add_item()
    dialog.close()


def test_calendar_and_upcoming_behavior(qapp, database, monkeypatch):
    today = date.today()
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO calendar_items (item_date, title, notes) VALUES (?, ?, ?)",
            (today.isoformat(), "Today", "Now"),
        )
        connection.execute(
            "INSERT INTO calendar_items (item_date, title, notes) VALUES (?, ?, ?)",
            ((today + timedelta(days=9)).isoformat(), "Later", "Later"),
        )

    page = HomePage(database)
    assert page.upcoming_list.count() == 1
    upcoming = page.upcoming_list.item(0)
    assert upcoming.data(UPCOMING_DATE_ROLE) == today.isoformat()

    opened = []
    monkeypatch.setattr(page, "_open_day", lambda selected: opened.append(selected))
    page._open_upcoming_item_date(upcoming)
    assert opened == [today]
    empty = SimpleNamespace(data=lambda role: None)
    page._open_upcoming_item_date(empty)

    previous_year = page.current_year
    page._change_year(1)
    assert page.current_year == previous_year + 1
    page._change_year(-1)

    counts = page._calendar_item_counts()
    assert counts[today.isoformat()] == 1
    assert "QPushButton" in page._day_button_stylesheet(today, counts)
    assert "QPushButton" in page._day_button_stylesheet(today + timedelta(days=1), counts)
    assert "QPushButton" in page._day_button_stylesheet(today, {})

    fake_day = SimpleNamespace(exec=lambda: QDialog.Accepted)
    monkeypatch.setattr(calendar_view, "CalendarDayDialog", lambda *args: fake_day)
    monkeypatch.delattr(page, "_open_day")
    page._open_day(today)
