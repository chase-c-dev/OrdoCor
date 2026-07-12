from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.services import backup_service as backup_module
from ordocor.services.backup_service import (
    LAST_BACKUP_CREATED_AT_KEY,
    BackupService,
    BackupValidationError,
)
from ordocor.services.local_security import PROTECTED_BACKUP_HEADER, LocalProtectionError
from ordocor.services.password_service import PasswordService
from ordocor.ui import main_window as main_window_module
from ordocor.ui.main_window import (
    MainWindow,
    SettingsDialog,
    _screen_capture_resistance_enabled,
)


def test_backup_create_restore_and_validation(database, tmp_path):
    service = BackupService(database)
    with database.connect() as connection:
        connection.execute("INSERT INTO projects (name) VALUES ('Original')")

    backup = service.create_backup(tmp_path / "folder" / "backup.sqlite3")
    assert backup.exists()
    assert backup.read_bytes().startswith(PROTECTED_BACKUP_HEADER)
    assert service.last_backup_created_at() is not None
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (LAST_BACKUP_CREATED_AT_KEY,),
            ).fetchone()[0]
            == service.last_backup_created_at()
        )
    service.validate_backup(backup)

    with database.connect() as connection:
        connection.execute("DELETE FROM projects")
    assert service.restore_backup(backup) == database.path
    with database.connect() as connection:
        assert connection.execute("SELECT name FROM projects").fetchone()[0] == "Original"

    with pytest.raises(BackupValidationError, match="does not exist"):
        service.validate_backup(tmp_path / "missing.sqlite3")

    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_text("not sqlite", encoding="utf-8")
    with pytest.raises(BackupValidationError, match="not a readable"):
        service.validate_backup(corrupt)

    legacy_backup = tmp_path / "legacy.sqlite3"
    with database.connect() as source:
        with backup_module.sqlite3.connect(legacy_backup) as destination:
            source.backup(destination)
    service.validate_backup(legacy_backup)


def test_backup_rejects_failed_integrity_check(database, tmp_path, monkeypatch):
    source = tmp_path / "backup.sqlite3"
    source.touch()

    class BadIntegrityConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql):
            return SimpleNamespace(fetchone=lambda: ("corrupt",))

    monkeypatch.setattr(
        backup_module.sqlite3,
        "connect",
        lambda *args, **kwargs: BadIntegrityConnection(),
    )
    with pytest.raises(BackupValidationError, match="integrity"):
        BackupService(database).validate_backup(source)


def test_backup_wraps_local_protection_errors(database, tmp_path, monkeypatch):
    monkeypatch.setattr(
        backup_module,
        "protect_backup_payload",
        lambda payload: (_ for _ in ()).throw(LocalProtectionError("locked")),
    )

    with pytest.raises(OSError, match="locked"):
        BackupService(database).create_backup(tmp_path / "backup.ordocorbackup")


def test_settings_backup_actions(qapp, database, theme_manager, monkeypatch, tmp_path):
    service = BackupService(database)
    password_service = PasswordService(database)
    dialog = SettingsDialog(service, password_service, theme_manager, None)
    messages = []
    protected = []
    monkeypatch.setattr(
        main_window_module,
        "apply_screen_capture_resistance",
        lambda widget: protected.append(widget) or True,
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args))
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: messages.append(args))
    assert dialog.last_backup_label.text() == "Last backup: Never"
    assert main_window_module._format_backup_timestamp("not a timestamp") == "Recorded"

    dialog.show()
    qapp.processEvents()
    assert dialog in protected

    monkeypatch.setattr(main_window_module.QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    dialog._create_backup()

    destination = tmp_path / "backup.sqlite3"
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *args: (str(destination), "SQLite"),
    )
    dialog._create_backup()
    assert destination.exists()
    assert dialog.last_backup_label.text().startswith("Last backup: ")
    assert dialog.last_backup_label.text() != "Last backup: Never"

    monkeypatch.setattr(
        service,
        "create_backup",
        lambda path: (_ for _ in ()).throw(OSError("C:/secret/user-data.sqlite3")),
    )
    dialog._create_backup()
    assert "secret" not in messages[-1][2]


def test_settings_restore_paths(qapp, database, theme_manager, monkeypatch, tmp_path):
    service = BackupService(database)
    password_service = PasswordService(database)
    dialog = SettingsDialog(service, password_service, theme_manager, None)
    source = tmp_path / "backup.sqlite3"
    BackupService(database).create_backup(source)
    messages = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args))
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: messages.append(args))

    monkeypatch.setattr(main_window_module.QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    dialog._load_backup()

    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileName",
        lambda *args: (str(source), "SQLite"),
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.No)
    dialog._load_backup()

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    monkeypatch.setattr(
        service,
        "restore_backup",
        lambda path: (_ for _ in ()).throw(BackupValidationError("bad")),
    )
    dialog._load_backup()

    monkeypatch.setattr(
        service,
        "restore_backup",
        lambda path: (_ for _ in ()).throw(OSError("C:/secret/user-data.sqlite3")),
    )
    dialog._load_backup()
    assert "secret" not in messages[-1][2]

    monkeypatch.setattr(service, "restore_backup", lambda path: database.path)
    dialog._load_backup()
    assert dialog.result() == QDialog.Accepted


def test_settings_password_actions(qapp, database, theme_manager, monkeypatch):
    service = BackupService(database)
    password_service = PasswordService(database)
    dialog = SettingsDialog(service, password_service, theme_manager, None)
    messages = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args))

    class NewPasswordDialog:
        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

        def password(self):
            return "new"

    monkeypatch.setattr(main_window_module, "PasswordChangeDialog", NewPasswordDialog)
    dialog._enable_password()
    assert password_service.verify_password("new") is True
    assert not dialog.enable_password_button.isEnabled()

    class WrongCurrentDialog(NewPasswordDialog):
        def current_password(self):
            return "wrong"

        def password(self):
            return "changed"

    monkeypatch.setattr(main_window_module, "PasswordChangeDialog", WrongCurrentDialog)
    dialog._change_password()
    assert password_service.verify_password("new") is True

    class CorrectCurrentDialog(WrongCurrentDialog):
        def current_password(self):
            return "new"

    monkeypatch.setattr(main_window_module, "PasswordChangeDialog", CorrectCurrentDialog)
    dialog._change_password()
    assert password_service.verify_password("changed") is True

    class WrongConfirm:
        def __init__(self, *args):
            pass

        def exec(self):
            return QDialog.Accepted

        def password(self):
            return "wrong"

    monkeypatch.setattr(main_window_module, "PasswordConfirmDialog", WrongConfirm)
    dialog._disable_password()
    assert password_service.is_enabled() is True

    class CorrectConfirm(WrongConfirm):
        def password(self):
            return "changed"

    monkeypatch.setattr(main_window_module, "PasswordConfirmDialog", CorrectConfirm)
    dialog._disable_password()
    assert password_service.is_enabled() is False
    assert dialog.enable_password_button.isEnabled()
    assert messages


def test_settings_password_actions_cancel(qapp, database, theme_manager, monkeypatch):
    service = BackupService(database)
    password_service = PasswordService(database)
    dialog = SettingsDialog(service, password_service, theme_manager, None)

    class CanceledDialog:
        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(main_window_module, "PasswordChangeDialog", CanceledDialog)
    dialog._enable_password()
    assert password_service.is_enabled() is False

    password_service.set_password("current")
    dialog._refresh_security_controls()
    dialog._change_password()
    assert password_service.verify_password("current") is True

    monkeypatch.setattr(main_window_module, "PasswordConfirmDialog", CanceledDialog)
    dialog._disable_password()
    assert password_service.is_enabled() is True


def test_settings_screen_capture_toggle(qapp, database, theme_manager, monkeypatch):
    service = BackupService(database)
    password_service = PasswordService(database)
    changed = []
    protected = []
    cleared = []
    monkeypatch.setattr(
        main_window_module,
        "apply_screen_capture_resistance",
        lambda widget: protected.append(widget) or True,
    )
    monkeypatch.setattr(
        main_window_module,
        "clear_screen_capture_resistance",
        lambda widget: cleared.append(widget) or True,
    )

    dialog = SettingsDialog(
        service,
        password_service,
        theme_manager,
        None,
        screen_security_changed=changed.append,
    )
    assert dialog.screen_security_checkbox.isChecked()
    assert _screen_capture_resistance_enabled(database) is True

    dialog.show()
    qapp.processEvents()
    assert dialog in protected

    dialog.screen_security_checkbox.setChecked(False)
    assert _screen_capture_resistance_enabled(database) is False
    assert changed[-1] is False
    assert dialog in cleared

    dialog.screen_security_checkbox.setChecked(True)
    assert _screen_capture_resistance_enabled(database) is True
    assert changed[-1] is True
    assert protected[-1] is dialog


def test_main_window_settings_refresh(qapp, database, theme_manager, monkeypatch):
    window = MainWindow(database, theme_manager)
    current_count = window.pages.count()

    monkeypatch.setattr(
        main_window_module,
        "SettingsDialog",
        lambda *args: SimpleNamespace(exec=lambda: QDialog.Rejected),
    )
    window._open_settings()
    assert window.pages.count() == current_count

    monkeypatch.setattr(
        main_window_module,
        "SettingsDialog",
        lambda *args: SimpleNamespace(exec=lambda: QDialog.Accepted),
    )
    window._open_settings()
    assert window.pages.count() == current_count
    window.close()


def test_main_window_screen_security_sync(qapp, database, theme_manager, monkeypatch):
    window = MainWindow(database, theme_manager)
    protected = []
    cleared = []
    monkeypatch.setattr(
        main_window_module,
        "apply_screen_capture_resistance",
        lambda widget: protected.append(widget) or True,
    )
    monkeypatch.setattr(
        main_window_module,
        "clear_screen_capture_resistance",
        lambda widget: cleared.append(widget) or True,
    )

    window._sync_screen_security(True)
    assert protected == [window]

    window._sync_screen_security(False)
    assert cleared == [window]

    window.close()
