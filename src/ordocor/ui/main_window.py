from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ordocor.data.database import Database
from ordocor.services.backup_service import BackupService, BackupValidationError
from ordocor.services.password_service import PasswordService
from ordocor.ui.animated_widgets import AnimatedStackedWidget
from ordocor.ui.branding import APP_DISPLAY_NAME, APP_RELEASE_LABEL, app_icon
from ordocor.ui.design_config import ANIMATION
from ordocor.ui.password_dialogs import (
    PasswordChangeDialog,
    PasswordConfirmDialog,
    PasswordSetupDialog,
    PasswordUnlockDialog,
)
from ordocor.ui.pages.home import HomePage
from ordocor.ui.pages.house import HousePage
from ordocor.ui.pages.investing import InvestingPage
from ordocor.ui.pages.projects import ProjectsPage
from ordocor.ui.pages.recipes import RecipesPage
from ordocor.ui.pages.travel import TravelPage
from ordocor.ui.pages.vehicle import VehiclePage
from ordocor.ui.pages.wishlist import WishlistPage
from ordocor.ui.screen_security import apply_screen_capture_resistance
from ordocor.ui.screen_security import clear_screen_capture_resistance
from ordocor.ui.theme import ThemeManager
from ordocor.ui.welcome import WelcomePage


SCREEN_CAPTURE_RESISTANCE_KEY = "screen_capture_resistance_enabled"


class SettingsDialog(QDialog):
    def __init__(
        self,
        backup_service: BackupService,
        password_service: PasswordService,
        theme_manager: ThemeManager,
        parent: QWidget,
        screen_security_changed=None,
    ) -> None:
        super().__init__(parent)
        self.backup_service = backup_service
        self.password_service = password_service
        self.theme_manager = theme_manager
        self.screen_security_changed = screen_security_changed
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        heading = QLabel("Database Backup")
        heading.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")

        description = QLabel(
            "Create a protected single-file backup of all OrdoCor data, or load a "
            "compatible OrdoCor backup into this app."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #D2C4AA;")
        self.last_backup_label = QLabel()
        self.last_backup_label.setWordWrap(True)
        self.last_backup_label.setStyleSheet("color: #B7A98F;")

        appearance_heading = QLabel("Appearance")
        appearance_heading.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        appearance_description = QLabel(
            "Choose a color palette. Changes preview immediately and are saved for the next launch."
        )
        appearance_description.setWordWrap(True)
        appearance_description.setStyleSheet("color: #D2C4AA;")

        palette_row = QHBoxLayout()
        palette_label = QLabel("Color Palette")
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.theme_manager.theme_names)
        self.palette_selector.setCurrentText(self.theme_manager.current_theme)
        self.palette_selector.currentTextChanged.connect(self.theme_manager.apply)
        palette_row.addWidget(palette_label)
        palette_row.addWidget(self.palette_selector, stretch=1)

        actions = QHBoxLayout()
        backup_button = QPushButton("Create Backup")
        restore_button = QPushButton("Load Backup")
        backup_button.clicked.connect(self._create_backup)
        restore_button.clicked.connect(self._load_backup)
        actions.addWidget(backup_button)
        actions.addWidget(restore_button)
        actions.addStretch()

        security_heading = QLabel("Security")
        security_heading.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        self.security_description = QLabel()
        self.security_description.setWordWrap(True)
        self.security_description.setStyleSheet("color: #D2C4AA;")
        self.screen_security_checkbox = QCheckBox("Reduce screen capture visibility")
        self.screen_security_checkbox.setChecked(_screen_capture_resistance_enabled(self.database))
        self.screen_security_checkbox.toggled.connect(self._set_screen_security_enabled)
        screen_security_note = QLabel(
            "Enabled by default. Turn this off when sharing your screen or recording OrdoCor."
        )
        screen_security_note.setWordWrap(True)
        screen_security_note.setStyleSheet("color: #B7A98F;")

        security_actions = QHBoxLayout()
        self.enable_password_button = QPushButton()
        self.change_password_button = QPushButton("Change Password")
        self.disable_password_button = QPushButton("Disable Password")
        self.enable_password_button.clicked.connect(self._enable_password)
        self.change_password_button.clicked.connect(self._change_password)
        self.disable_password_button.clicked.connect(self._disable_password)
        security_actions.addWidget(self.enable_password_button)
        security_actions.addWidget(self.change_password_button)
        security_actions.addWidget(self.disable_password_button)
        security_actions.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout.addWidget(appearance_heading)
        layout.addWidget(appearance_description)
        layout.addLayout(palette_row)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(self.last_backup_label)
        layout.addLayout(actions)
        layout.addWidget(security_heading)
        layout.addWidget(self.security_description)
        layout.addWidget(self.screen_security_checkbox)
        layout.addWidget(screen_security_note)
        layout.addLayout(security_actions)
        layout.addWidget(buttons)
        self._refresh_security_controls()
        self._refresh_backup_status()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_screen_security_for_dialog()

    @property
    def database(self) -> Database:
        return self.backup_service.database

    def _create_backup(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Backup OrdoCor Database",
            "ordocor_backup.ordocorbackup",
            "Protected OrdoCor Backup (*.ordocorbackup);;SQLite Database (*.sqlite3)",
        )
        if not destination:
            return

        try:
            backup_path = self.backup_service.create_backup(Path(destination))
        except OSError:
            QMessageBox.critical(
                self,
                "Backup Failed",
                "OrdoCor could not create the backup. Check the selected folder and try again.",
            )
            return
        self._refresh_backup_status()

        QMessageBox.information(
            self,
            "Backup Complete",
            f"Database backup created:\n{backup_path}",
        )

    def _load_backup(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Load OrdoCor Database Backup",
            "",
            "OrdoCor Backup (*.ordocorbackup *.sqlite3 *.db);;All Files (*)",
        )
        if not source:
            return

        confirmed = QMessageBox.question(
            self,
            "Load Backup",
            "Loading a backup will replace the current local OrdoCor database. Continue?",
        )
        if confirmed != QMessageBox.Yes:
            return

        try:
            restored_path = self.backup_service.restore_backup(Path(source))
        except BackupValidationError as error:
            QMessageBox.critical(self, "Invalid Backup", str(error))
            return
        except OSError:
            QMessageBox.critical(
                self,
                "Restore Failed",
                "OrdoCor could not load the selected backup. Check the file and try again.",
            )
            return

        QMessageBox.information(
            self,
            "Backup Loaded",
            f"Database backup loaded:\n{restored_path}",
        )
        self.accept()

    def _enable_password(self) -> None:
        dialog = PasswordChangeDialog(require_current=False, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        self.password_service.set_password(dialog.password())
        QMessageBox.information(
            self, "Password Enabled", "OrdoCor will ask for a password on entry."
        )
        self._refresh_security_controls()

    def _change_password(self) -> None:
        dialog = PasswordChangeDialog(require_current=True, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not self.password_service.verify_password(dialog.current_password()):
            QMessageBox.warning(self, "Incorrect Password", "The current password was not correct.")
            return

        self.password_service.set_password(dialog.password())
        QMessageBox.information(self, "Password Updated", "Your OrdoCor password was updated.")
        self._refresh_security_controls()

    def _disable_password(self) -> None:
        dialog = PasswordConfirmDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not self.password_service.verify_password(dialog.password()):
            QMessageBox.warning(self, "Incorrect Password", "The current password was not correct.")
            return

        self.password_service.disable_password()
        QMessageBox.information(
            self,
            "Password Disabled",
            "OrdoCor will open without asking for a password.",
        )
        self._refresh_security_controls()

    def _set_screen_security_enabled(self, enabled: bool) -> None:
        _set_screen_capture_resistance_enabled(self.database, enabled)
        self._sync_screen_security_for_dialog()
        if self.screen_security_changed is not None:
            self.screen_security_changed(enabled)

    def _sync_screen_security_for_dialog(self) -> None:
        if self.screen_security_checkbox.isChecked():
            apply_screen_capture_resistance(self)
        else:
            clear_screen_capture_resistance(self)

    def _refresh_security_controls(self) -> None:
        enabled = self.password_service.is_enabled()
        if enabled:
            self.security_description.setText(
                "Password protection is enabled. OrdoCor will ask for your password after "
                "the welcome screen."
            )
            self.enable_password_button.setText("Password Enabled")
        else:
            self.security_description.setText(
                "Password protection is disabled. You can enable it without changing the "
                "current Windows-bound database and backup protections."
            )
            self.enable_password_button.setText("Enable Password")

        self.enable_password_button.setEnabled(not enabled)
        self.change_password_button.setEnabled(enabled)
        self.disable_password_button.setEnabled(enabled)

    def _refresh_backup_status(self) -> None:
        timestamp = self.backup_service.last_backup_created_at()
        if timestamp is None:
            self.last_backup_label.setText("Last backup: Never")
            return

        self.last_backup_label.setText(f"Last backup: {_format_backup_timestamp(timestamp)}")


class MainWindow(QMainWindow):
    def __init__(self, database: Database, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.database = database
        self.backup_service = BackupService(database)
        self.password_service = PasswordService(database)
        self.theme_manager = theme_manager

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(app_icon())
        self._build_ui()
        self.theme_manager.refresh_widget(self)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_screen_security()

    def _build_ui(self) -> None:
        self.shell_stack = AnimatedStackedWidget(duration_ms=ANIMATION["welcome_fade_ms"])
        self.welcome_page = WelcomePage()
        self.welcome_page.enter_requested.connect(self._handle_welcome_entry)

        root = QWidget()
        root.setObjectName("appRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.pages = AnimatedStackedWidget()
        self._populate_pages()

        layout.addWidget(sidebar)
        layout.addWidget(self.pages, stretch=1)

        self.shell_stack.addWidget(self.welcome_page)
        self.shell_stack.addWidget(root)
        self.setCentralWidget(self.shell_stack)

    def _populate_pages(self) -> None:
        while self.pages.count():
            widget = self.pages.widget(0)
            self.pages.removeWidget(widget)
            widget.deleteLater()

        self.pages.addWidget(HomePage(database=self.database))
        self.pages.addWidget(InvestingPage(database=self.database))
        self.pages.addWidget(RecipesPage(database=self.database))
        self.pages.addWidget(ProjectsPage(database=self.database))
        self.pages.addWidget(WishlistPage(database=self.database))
        self.pages.addWidget(TravelPage(database=self.database))
        self.pages.addWidget(HousePage(database=self.database))
        self.pages.addWidget(VehiclePage(database=self.database))
        self.theme_manager.refresh_widget(self.pages)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            """
            QWidget#sidebar {
                background: #130E11;
                border-right: 1px solid #3B2D32;
            }
            """
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(16)

        title = QLabel(APP_DISPLAY_NAME)
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #F3E7C9;")

        subtitle = QLabel(f"Life dashboard | {APP_RELEASE_LABEL}")
        subtitle.setStyleSheet("color: #9B8F83; font-size: 12px;")

        self.navigation = QListWidget()
        self.navigation.addItem(QListWidgetItem("Home"))
        self.navigation.addItem(QListWidgetItem("Investing"))
        self.navigation.addItem(QListWidgetItem("Recipes"))
        self.navigation.addItem(QListWidgetItem("Projects"))
        self.navigation.addItem(QListWidgetItem("Wishlist"))
        self.navigation.addItem(QListWidgetItem("Travel"))
        self.navigation.addItem(QListWidgetItem("House"))
        self.navigation.addItem(QListWidgetItem("Vehicle"))
        self.navigation.setCurrentRow(0)
        self.navigation.currentRowChanged.connect(self._show_page)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self._open_settings)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.navigation, stretch=1)
        layout.addWidget(settings_button)

        return sidebar

    def _show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)

    def _handle_welcome_entry(self) -> None:
        if not self._password_entry_allowed():
            return
        self._enter_application()

    def _password_entry_allowed(self) -> bool:
        if self.password_service.is_enabled():
            dialog = PasswordUnlockDialog(self)
            if dialog.exec() != QDialog.Accepted:
                self.welcome_page.reset_after_denied("Locked. Enter when ready.")
                return False
            if not self.password_service.verify_password(dialog.password()):
                QMessageBox.warning(self, "Incorrect Password", "The password was not correct.")
                self.welcome_page.reset_after_denied("Locked. Try again.")
                return False
            return True

        if not self.password_service.has_seen_setup_prompt():
            dialog = PasswordSetupDialog(self)
            if dialog.exec() == QDialog.Accepted:
                self.password_service.set_password(dialog.password())
            else:
                self.password_service.mark_setup_prompt_seen()
        return True

    def _enter_application(self) -> None:
        self.shell_stack.setCurrentIndex(1)

    def _open_settings(self) -> None:
        current_index = self.pages.currentIndex()
        dialog = SettingsDialog(
            self.backup_service,
            self.password_service,
            self.theme_manager,
            self,
            self._handle_screen_security_changed,
        )
        if dialog.exec() == QDialog.Accepted:
            self._populate_pages()
            self.pages.setCurrentIndex(min(current_index, self.pages.count() - 1))

    def _handle_screen_security_changed(self, enabled: bool) -> None:
        self._sync_screen_security(enabled)

    def _sync_screen_security(self, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = _screen_capture_resistance_enabled(self.database)
        if enabled:
            apply_screen_capture_resistance(self)
        else:
            clear_screen_capture_resistance(self)


def _format_backup_timestamp(timestamp: str) -> str:
    try:
        return datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %I:%M %p %Z").strip()
    except ValueError:
        return "Recorded"


def _screen_capture_resistance_enabled(database: Database) -> bool:
    with database.connect() as connection:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (SCREEN_CAPTURE_RESISTANCE_KEY,),
        ).fetchone()
    if row is None:
        return True
    return row["value"] == "1"


def _set_screen_capture_resistance_enabled(database: Database, enabled: bool) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (SCREEN_CAPTURE_RESISTANCE_KEY, "1" if enabled else "0"),
        )
