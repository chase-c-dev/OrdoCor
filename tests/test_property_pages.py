from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.ui.pages.house import page as house_module
from ordocor.ui.pages.house.page import HousePage
from ordocor.ui.pages.vehicle import page as vehicle_module
from ordocor.ui.pages.vehicle.page import VehiclePage


def fake_dialog(data_method: str, data: dict[str, object], result=QDialog.Accepted):
    return SimpleNamespace(exec=lambda: result, **{data_method: lambda: data})


def test_house_page_workflows(qapp, database, monkeypatch):
    page = HousePage(database)
    opened_urls = []
    monkeypatch.setattr(
        house_module.QDesktopServices, "openUrl", lambda url: opened_urls.append(url)
    )
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)

    reminder = {
        "name": "Property Taxes",
        "reminder_type": "Tax",
        "due_date": "2026-10-01",
        "amount": 1200,
        "notes": "County bill",
    }
    monkeypatch.setattr(
        house_module,
        "HouseReminderDialog",
        lambda *args: fake_dialog("reminder_data", reminder),
    )
    page._add_reminder()
    assert page.reminders_table.rowCount() == 1
    page.reminders_table.setCurrentCell(0, 0)
    page._modify_reminder()

    rejected = fake_dialog("reminder_data", reminder, QDialog.Rejected)
    monkeypatch.setattr(house_module, "HouseReminderDialog", lambda *args: rejected)
    page._modify_reminder()

    invalid = dict(reminder, name="")
    monkeypatch.setattr(
        house_module,
        "HouseReminderDialog",
        lambda *args: fake_dialog("reminder_data", invalid),
    )
    page._modify_reminder()
    assert page._validate_required(invalid, "name", "Missing") is False
    page._add_reminder()
    monkeypatch.setattr(
        house_module,
        "HouseReminderDialog",
        lambda *args: fake_dialog("reminder_data", reminder, QDialog.Rejected),
    )
    page._add_reminder()
    page.reminders_table.setCurrentCell(0, 0)
    page._modify_reminder()
    with database.connect() as connection:
        connection.execute("DELETE FROM house_reminders")
    page._modify_reminder()

    maintenance = {
        "title": "Furnace Filter",
        "frequency": "Quarterly",
        "due_date": "2026-08-01",
        "video_url": "https://youtube.com/watch?v=filter",
        "notes": "MERV 11",
    }
    monkeypatch.setattr(
        house_module,
        "HouseMaintenanceDialog",
        lambda *args: fake_dialog("maintenance_data", maintenance),
    )
    page._add_maintenance()
    assert page.maintenance_table.rowCount() == 1
    page.maintenance_table.setCurrentCell(0, 0)
    page._modify_maintenance()
    page.maintenance_table.setCurrentCell(0, 0)
    page._open_maintenance_link()
    assert opened_urls[-1].toString() == maintenance["video_url"]

    improvement = {
        "name": "Patio",
        "priority": "Medium",
        "estimated_cost": 5000,
        "notes": "Stone",
    }
    monkeypatch.setattr(
        house_module,
        "HouseImprovementDialog",
        lambda *args: fake_dialog("improvement_data", improvement),
    )
    page._add_improvement()
    assert page.improvements_table.rowCount() == 1
    page.improvements_table.setCurrentCell(0, 0)
    page._modify_improvement()
    monkeypatch.setattr(
        house_module,
        "HouseImprovementDialog",
        lambda *args: fake_dialog("improvement_data", dict(improvement, name="")),
    )
    page.improvements_table.setCurrentCell(0, 0)
    page._modify_improvement()

    with database.connect() as connection:
        connection.execute("DELETE FROM house_improvements")
    page._modify_improvement()

    page.reminders_table.setCurrentCell(0, 0)
    page._remove_reminder()
    assert page.reminders_table.rowCount() == 0
    page.maintenance_table.setCurrentCell(0, 0)
    page._remove_maintenance()
    assert page.maintenance_table.rowCount() == 0
    page.improvements_table.setCurrentCell(0, 0)
    page._remove_improvement()
    assert page.improvements_table.rowCount() == 0

    page._remove_reminder()
    assert page._money(12.5) == "$12.50"
    assert page._preview("a " * 100).endswith("...")


def test_vehicle_page_workflows(qapp, database, monkeypatch):
    page = VehiclePage(database)
    opened_urls = []
    monkeypatch.setattr(
        vehicle_module.QDesktopServices, "openUrl", lambda url: opened_urls.append(url)
    )
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)

    page._add_maintenance()
    assert page.maintenance_table.rowCount() == 0
    page._modify_vehicle()
    page._modify_maintenance()
    page._remove_maintenance()
    page._add_wishlist_item()
    page._modify_wishlist_item()
    page._remove_wishlist_item()

    vehicle = {
        "name": "Truck",
        "make": "Example Make",
        "model": "Example Model",
        "vehicle_year": 2024,
        "vin": "123",
        "notes": "Blue",
    }
    monkeypatch.setattr(
        vehicle_module,
        "VehicleDialog",
        lambda *args: fake_dialog("vehicle_data", vehicle),
    )
    page._add_vehicle()
    assert page.vehicle_table.rowCount() == 1
    page.vehicle_table.setCurrentCell(0, 0)
    page._modify_vehicle()

    invalid_vehicle = dict(vehicle, name="")
    monkeypatch.setattr(
        vehicle_module,
        "VehicleDialog",
        lambda *args: fake_dialog("vehicle_data", invalid_vehicle),
    )
    page._modify_vehicle()
    page._add_vehicle()
    monkeypatch.setattr(
        vehicle_module,
        "VehicleDialog",
        lambda *args: fake_dialog("vehicle_data", vehicle, QDialog.Rejected),
    )
    page._add_vehicle()
    page.vehicle_table.setCurrentCell(0, 0)
    page._modify_vehicle()
    with database.connect() as connection:
        connection.execute("DELETE FROM vehicles")
    page._modify_vehicle()

    monkeypatch.setattr(
        vehicle_module,
        "VehicleDialog",
        lambda *args: fake_dialog("vehicle_data", vehicle),
    )
    page._add_vehicle()
    page.vehicle_table.setCurrentCell(0, 0)

    maintenance = {
        "title": "Oil Change",
        "due_date": "2026-09-01",
        "video_url": "https://youtube.com/watch?v=oil",
        "notes": "Synthetic",
    }
    monkeypatch.setattr(
        vehicle_module,
        "VehicleMaintenanceDialog",
        lambda *args: fake_dialog("maintenance_data", maintenance),
    )
    page._add_maintenance()
    assert page.maintenance_table.rowCount() == 1
    page.maintenance_table.setCurrentCell(0, 0)
    page._modify_maintenance()
    page.maintenance_table.setCurrentCell(0, 0)
    page._open_maintenance_link()
    assert opened_urls[-1].toString() == maintenance["video_url"]
    invalid_maintenance = dict(maintenance, title="")
    monkeypatch.setattr(
        vehicle_module,
        "VehicleMaintenanceDialog",
        lambda *args: fake_dialog("maintenance_data", invalid_maintenance),
    )
    page._add_maintenance()
    page.maintenance_table.setCurrentCell(0, 0)
    page._modify_maintenance()
    monkeypatch.setattr(
        vehicle_module,
        "VehicleMaintenanceDialog",
        lambda *args: fake_dialog("maintenance_data", maintenance, QDialog.Rejected),
    )
    page._add_maintenance()
    page._modify_maintenance()
    with database.connect() as connection:
        connection.execute("DELETE FROM vehicle_maintenance")
    page._modify_maintenance()

    wishlist = {
        "item_name": "Floor Mats",
        "category": "Interior",
        "estimated_price": 120,
        "notes": "All weather",
    }
    monkeypatch.setattr(
        vehicle_module,
        "VehicleWishlistDialog",
        lambda *args: fake_dialog("wishlist_data", wishlist),
    )
    page._add_wishlist_item()
    assert page.vehicle_wishlist_table.rowCount() == 1
    page.vehicle_wishlist_table.setCurrentCell(0, 0)
    page._modify_wishlist_item()
    invalid_wishlist = dict(wishlist, item_name="")
    monkeypatch.setattr(
        vehicle_module,
        "VehicleWishlistDialog",
        lambda *args: fake_dialog("wishlist_data", invalid_wishlist),
    )
    page._add_wishlist_item()
    page.vehicle_wishlist_table.setCurrentCell(0, 0)
    page._modify_wishlist_item()
    monkeypatch.setattr(
        vehicle_module,
        "VehicleWishlistDialog",
        lambda *args: fake_dialog("wishlist_data", wishlist, QDialog.Rejected),
    )
    page._add_wishlist_item()
    page._modify_wishlist_item()

    with database.connect() as connection:
        connection.execute("DELETE FROM vehicle_wishlist")
    page._modify_wishlist_item()

    page.maintenance_table.setCurrentCell(0, 0)
    page._remove_maintenance()
    assert page.maintenance_table.rowCount() == 0
    page.vehicle_wishlist_table.setCurrentCell(0, 0)
    page._remove_wishlist_item()
    assert page.vehicle_wishlist_table.rowCount() == 0

    page.vehicle_table.setCurrentCell(0, 0)
    page._remove_vehicle()
    assert page.vehicle_table.rowCount() == 0
    page._remove_vehicle()
    assert page._money(12.5) == "$12.50"
    assert page._preview("a " * 100).endswith("...")
