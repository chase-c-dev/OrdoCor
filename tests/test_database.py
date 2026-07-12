import sqlite3

from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from ordocor.data.database import Database
from ordocor.services.backup_service import BackupService, BackupValidationError
from ordocor.ui.design_config import BUTTON, FONT, TAB
from ordocor.ui.theme import (
    DEFAULT_THEME,
    PALETTES,
    ThemeManager,
    stylesheet_for,
    themed_stylesheet,
)


def test_database_initializes_schema(tmp_path):
    database = Database(tmp_path / "ordocor.sqlite3")
    database.initialize()

    with database.connect() as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

    assert "investment_accounts" in tables
    assert "investment_holdings" in tables
    assert "investment_transactions" in tables
    assert "investment_watchlist" in tables
    assert "investment_stocks" in tables
    assert "investment_mutual_funds" in tables
    assert "investment_banking_products" in tables
    assert "investment_pipeline" in tables
    assert "investment_collectibles" in tables
    assert "todo_items" in tables
    assert "calendar_items" in tables
    assert "recipes" in tables
    assert "recipe_categories" in tables
    assert "projects" in tables
    assert "wishlist_items" in tables
    assert "travel_destinations" in tables
    assert "vehicles" in tables
    assert "vehicle_maintenance" in tables
    assert "vehicle_wishlist" in tables
    assert "house_reminders" in tables
    assert "house_maintenance" in tables
    assert "house_improvements" in tables
    assert "app_settings" in tables

    with database.connect() as connection:
        stock_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(investment_stocks)")
        }
    assert {"market_price", "dividend_yield", "market_updated_at"} <= stock_columns

    with database.connect() as connection:
        fund_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(investment_mutual_funds)")
        }
    assert {"market_price", "dividend_yield", "market_updated_at"} <= fund_columns


def test_backup_validation_rejects_non_ordocor_database(tmp_path):
    invalid_backup = tmp_path / "invalid.sqlite3"
    sqlite3.connect(invalid_backup).close()

    database = Database(tmp_path / "ordocor.sqlite3")
    service = BackupService(database)

    try:
        service.validate_backup(invalid_backup)
    except BackupValidationError:
        return

    raise AssertionError("Expected invalid backup to be rejected")


def test_moonlit_is_default_and_selected_theme_persists(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "ordocor.sqlite3")
    database.initialize()

    manager = ThemeManager(database, app)
    assert DEFAULT_THEME == "Moonlit"
    assert manager.current_theme == "Moonlit"
    assert PALETTES["Moonlit"]["focus"] == "#7FA6D2"
    assert "#7FA6D2" in themed_stylesheet("border: 1px solid #C0A361;")
    assert f"border-radius: {BUTTON['radius']}px;" in stylesheet_for("Moonlit")
    assert "#7FA6D2" in stylesheet_for("Moonlit")
    assert "#C0A361" in stylesheet_for("Medieval")
    assert f"font-family: {FONT['family']};" in stylesheet_for("Moonlit")
    assert f"border-radius: {BUTTON['radius']}px;" in stylesheet_for("Moonlit")
    assert f"min-width: {TAB['min_width']}px;" in stylesheet_for("Moonlit")
    assert f"padding-top: {BUTTON['pressed_padding_top']}px;" in stylesheet_for("Moonlit")

    button = QPushButton("Next")
    manager._prepare_button_feedback(button)
    manager._prepare_button_feedback(button)
    assert button.property("ordocor_button_feedback_connected") is True
    button.click()
    assert button.graphicsEffect() is not None
    assert button in manager._button_animations
    effect = button.graphicsEffect()
    manager._clear_button_animation(button, effect)
    assert button.graphicsEffect() is None

    button.setEnabled(False)
    manager._animate_button(button)
    assert button.graphicsEffect() is None

    manager.apply("Woodland")
    restored_manager = ThemeManager(database, app)
    assert restored_manager.current_theme == "Woodland"

    manager.apply("not-a-theme")
    assert manager.current_theme == "Woodland"

    widget = QWidget()
    widget.setStyleSheet("color: #EDF3EF;")
    widget.show()
    manager.apply("Moonlit", persist=False)
    assert manager.current_theme == "Moonlit"
    widget.close()
    manager.close()
    restored_manager.close()
    manager.setParent(None)
    restored_manager.setParent(None)
    manager.deleteLater()
    restored_manager.deleteLater()
    app.processEvents()
