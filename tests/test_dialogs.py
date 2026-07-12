from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit, QSpinBox

from ordocor.ui.pages.home.dialogs import TextItemDialog
from ordocor.ui.pages.house.page import (
    HouseImprovementDialog,
    HouseMaintenanceDialog,
    HouseReminderDialog,
)
from ordocor.ui.pages.investing.accounts import AccountDialog
from ordocor.ui.pages.investing.banking import CertificateOfDepositDialog
from ordocor.ui.pages.investing.collectibles import CollectibleDialog
from ordocor.ui.pages.investing.mutual_funds import MutualFundDialog
from ordocor.ui.pages.investing.plans import InvestmentPlanDialog
from ordocor.ui.pages.investing.stocks import StockDialog
from ordocor.ui.pages.projects.dialog import ProjectDialog
from ordocor.ui.pages.recipes.dialog import RecipeDialog
from ordocor.ui.pages.travel.dialog import TravelDestinationDialog
from ordocor.ui.pages.vehicle.page import (
    VehicleDialog,
    VehicleMaintenanceDialog,
    VehicleWishlistDialog,
)
from ordocor.ui.pages.wishlist.dialog import WishlistItemDialog
from ordocor.ui.theme.stylesheet import set_active_theme


def test_home_text_item_dialog(qapp):
    dialog = TextItemDialog("Edit", None, "Title", "Notes")
    item = dialog.item()
    assert item.title == "Title"
    assert item.notes == "Notes"
    dialog.close()


def test_investing_dialogs_round_trip(qapp):
    account = AccountDialog(
        None,
        "Account",
        {"institution": "Bank", "name": "Main", "account_type": "checking"},
    )
    assert account.account_data() == {
        "institution": "Bank",
        "name": "Main",
        "account_type": "checking",
    }

    stock = StockDialog(
        None,
        "Stock",
        {
            "stock_name": "Example",
            "ticker": "ex",
            "purchase_date": "2026-01-02",
            "purchase_price": 12.5,
            "shares": 3.25,
            "target_sell_price": 20,
        },
    )
    assert stock.stock_data()["ticker"] == "EX"
    assert stock.stock_data()["purchase_date"] == "2026-01-02"

    fund = MutualFundDialog(
        None,
        "Fund",
        {
            "fund_name": "Fund",
            "symbol": "fund",
            "purchase_date": "2026-02-03",
            "purchase_price": 5,
            "shares": 10,
        },
    )
    assert fund.fund_data()["symbol"] == "FUND"

    cd = CertificateOfDepositDialog(
        None,
        "CD",
        {
            "product_name": "12 Month",
            "institution": "Bank",
            "open_date": "2026-01-01",
            "principal": 1000,
            "interest_rate": 4.25,
            "maturity_date": "2027-01-01",
            "maturity_value": 1042.5,
        },
    )
    assert cd.cd_data()["interest_rate"] == 4.25

    collectible = CollectibleDialog(
        None,
        "Collectible",
        {"item_name": "Coin", "category": "Coin", "target_price": 50, "quantity": 2},
    )
    assert collectible.collectible_data()["quantity"] == 2

    plan = InvestmentPlanDialog(
        None,
        "Plan",
        {
            "idea_name": "Index",
            "investment_type": "Mutual Fund",
            "desired_purchase_price": 100,
            "desired_shares": 4,
            "notes": "<b>Research</b>",
        },
    )
    plan._toggle_bold()
    plan._toggle_bold()
    plan._toggle_italic()
    plan._toggle_underline()
    plan._insert_bullets()
    assert plan.plan_data()["investment_type"] == "Mutual Fund"

    for dialog in (account, stock, fund, cd, collectible, plan):
        dialog.close()


def test_life_module_dialogs_round_trip(qapp):
    set_active_theme("Rosewood")
    project = ProjectDialog(None, "Project", {"name": "OrdoCor", "description": "Build it"})
    assert project.project_data() == {"name": "OrdoCor", "description": "Build it"}

    recipe = RecipeDialog(
        None,
        "Recipe",
        ["Dinner", "Dessert"],
        {
            "name": "Soup",
            "category": "Dinner",
            "servings": 4,
            "prep_minutes": 10,
            "cook_minutes": 30,
            "ingredients": "Water",
            "instructions": "Cook",
            "notes": "Warm",
        },
    )
    recipe.servings_input.resize(120, 40)
    recipe.servings_input.show()
    qapp.processEvents()
    QTest.mouseClick(recipe.servings_input, Qt.LeftButton, pos=QPoint(110, 8))
    assert recipe.recipe_data()["category"] == "Dinner"
    assert recipe.recipe_data()["servings"] == 5
    assert recipe._section_label("Test").text() == "Test"

    travel = TravelDestinationDialog(
        None,
        "Travel",
        {
            "country": "Japan",
            "city": "Tokyo",
            "priority": "high",
            "target_season": "Spring",
            "target_year": 2027,
            "notes": "Visit",
        },
    )
    assert isinstance(travel.year_input, QLineEdit)
    assert not isinstance(travel.year_input, QSpinBox)
    assert travel.destination_data()["target_year"] == 2027

    wishlist = WishlistItemDialog(
        None,
        "Wishlist",
        {
            "name": "Chair",
            "category": "Home",
            "estimated_price": 200,
            "quantity": 2,
            "notes": "Oak",
        },
    )
    assert wishlist.wishlist_data()["estimated_price"] == 200

    house_reminder = HouseReminderDialog(
        None,
        "Reminder",
        {
            "name": "Property Taxes",
            "reminder_type": "Tax",
            "due_date": "2026-10-01",
            "amount": 1200,
            "notes": "County",
        },
    )
    assert house_reminder.reminder_data()["amount"] == 1200
    due_date_input = house_reminder.inputs["due_date"]
    saturday_format = due_date_input.calendarWidget().weekdayTextFormat(Qt.Saturday)
    assert saturday_format.foreground().color().name() == "#f3e7e1"

    house_maintenance = HouseMaintenanceDialog(
        None,
        "Maintenance",
        {
            "title": "Furnace Filter",
            "frequency": "Quarterly",
            "due_date": "2026-08-01",
            "video_url": "https://youtube.com/watch?v=house",
            "notes": "MERV 11",
        },
    )
    assert house_maintenance.maintenance_data()["video_url"].startswith("https://")

    house_improvement = HouseImprovementDialog(
        None,
        "Improvement",
        {"name": "Patio", "priority": "Medium", "estimated_cost": 5000, "notes": "Stone"},
    )
    assert house_improvement.improvement_data()["estimated_cost"] == 5000

    vehicle = VehicleDialog(
        None,
        "Vehicle",
        {
            "name": "Truck",
            "make": "Example Make",
            "model": "Example Model",
            "vehicle_year": 2024,
            "vin": "123",
            "notes": "Blue",
        },
    )
    assert isinstance(vehicle.inputs["vehicle_year"], QLineEdit)
    assert not isinstance(vehicle.inputs["vehicle_year"], QSpinBox)
    assert vehicle.vehicle_data()["vehicle_year"] == 2024

    vehicle_maintenance = VehicleMaintenanceDialog(
        None,
        "Vehicle Maintenance",
        {
            "title": "Oil Change",
            "due_date": "2026-09-01",
            "video_url": "https://youtube.com/watch?v=oil",
            "notes": "Synthetic",
        },
    )
    assert vehicle_maintenance.maintenance_data()["title"] == "Oil Change"

    vehicle_wishlist = VehicleWishlistDialog(
        None,
        "Vehicle Wishlist",
        {
            "item_name": "Floor Mats",
            "category": "Interior",
            "estimated_price": 120,
            "notes": "All weather",
        },
    )
    assert vehicle_wishlist.wishlist_data()["estimated_price"] == 120

    for dialog in (
        project,
        recipe,
        travel,
        wishlist,
        house_reminder,
        house_maintenance,
        house_improvement,
        vehicle,
        vehicle_maintenance,
        vehicle_wishlist,
    ):
        dialog.close()
