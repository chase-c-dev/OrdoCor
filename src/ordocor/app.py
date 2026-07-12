import sys

from PySide6.QtWidgets import QApplication

from ordocor.data.database import Database
from ordocor.ui.branding import APP_DISPLAY_NAME, app_icon
from ordocor.ui.main_window import MainWindow
from ordocor.ui.theme import ThemeManager


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setOrganizationName(APP_DISPLAY_NAME)
    app.setWindowIcon(app_icon())

    database = Database.default()
    database.initialize()
    theme_manager = ThemeManager(database, app)

    window = MainWindow(database=database, theme_manager=theme_manager)
    window.resize(1200, 760)
    window.show()

    return app.exec()
