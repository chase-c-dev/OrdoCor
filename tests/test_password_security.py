from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from ordocor.services.password_service import (
    PASSWORD_HASH_KEY,
    PASSWORD_ITERATIONS_KEY,
    PASSWORD_PROMPT_SEEN_KEY,
    PASSWORD_SALT_KEY,
    PasswordService,
)
from ordocor.ui import main_window as main_window_module
from ordocor.ui.main_window import MainWindow
from ordocor.ui.password_dialogs import (
    PasswordChangeDialog,
    PasswordConfirmDialog,
    PasswordSetupDialog,
    PasswordUnlockDialog,
)


def test_password_service_lifecycle(database):
    service = PasswordService(database)

    assert service.has_seen_setup_prompt() is False
    assert service.is_enabled() is False
    assert service.verify_password("anything") is False
    with pytest.raises(ValueError, match="empty"):
        service.set_password("")

    service.mark_setup_prompt_seen()
    assert service.has_seen_setup_prompt() is True

    service.set_password("correct")
    assert service.is_enabled() is True
    assert service.verify_password("wrong") is False
    assert service.verify_password("correct") is True

    with database.connect() as connection:
        stored_hash = connection.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (PASSWORD_HASH_KEY,),
        ).fetchone()[0]
    assert stored_hash != "correct"

    with database.connect() as connection:
        connection.execute(
            "UPDATE app_settings SET value = 'not-base64' WHERE key = ?",
            (PASSWORD_SALT_KEY,),
        )
    assert service.verify_password("correct") is False

    service.set_password("correct")
    with database.connect() as connection:
        connection.execute(
            "UPDATE app_settings SET value = 'nope' WHERE key = ?",
            (PASSWORD_ITERATIONS_KEY,),
        )
    assert service.verify_password("correct") is False

    service.disable_password()
    assert service.is_enabled() is False
    assert service.has_seen_setup_prompt() is True


def test_password_dialog_validation(qapp, monkeypatch):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    setup = PasswordSetupDialog()
    setup._accept_password()
    assert setup.result() == QDialog.Rejected
    setup.password_input.setText("one")
    setup.confirm_input.setText("two")
    setup._accept_password()
    assert setup.result() == QDialog.Rejected
    setup.confirm_input.setText("one")
    setup._accept_password()
    assert setup.result() == QDialog.Accepted
    assert setup.password() == "one"
    setup.close()

    change = PasswordChangeDialog(require_current=True)
    change._accept_password()
    assert change.result() == QDialog.Rejected
    change.current_input.setText("old")
    change._accept_password()
    assert change.result() == QDialog.Rejected
    change.password_input.setText("new")
    change.confirm_input.setText("different")
    change._accept_password()
    assert change.result() == QDialog.Rejected
    change.confirm_input.setText("new")
    change._accept_password()
    assert change.result() == QDialog.Accepted
    assert change.current_password() == "old"
    assert change.password() == "new"
    change.close()

    unlock = PasswordUnlockDialog()
    unlock.password_input.setText("secret")
    assert unlock.password() == "secret"
    unlock.close()

    confirm = PasswordConfirmDialog()
    confirm.password_input.setText("secret")
    assert confirm.password() == "secret"
    confirm.close()
    assert warnings


def test_main_window_first_run_password_setup_paths(qapp, database, theme_manager, monkeypatch):
    window = MainWindow(database, theme_manager)

    class AcceptedSetup:
        def __init__(self, *args):
            pass

        def exec(self):
            return QDialog.Accepted

        def password(self):
            return "created"

    monkeypatch.setattr(main_window_module, "PasswordSetupDialog", AcceptedSetup)
    window._handle_welcome_entry()
    assert window.shell_stack.currentIndex() == 1
    assert window.password_service.verify_password("created") is True
    window.close()
    window.deleteLater()
    qapp.processEvents()

    second_window = MainWindow(database, theme_manager)
    second_window.password_service.disable_password()
    with database.connect() as connection:
        connection.execute(
            "DELETE FROM app_settings WHERE key = ?",
            (PASSWORD_PROMPT_SEEN_KEY,),
        )

    class RejectedSetup:
        def __init__(self, *args):
            pass

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(main_window_module, "PasswordSetupDialog", RejectedSetup)
    second_window._handle_welcome_entry()
    assert second_window.shell_stack.currentIndex() == 1
    assert second_window.password_service.has_seen_setup_prompt() is True
    second_window.close()
    second_window.deleteLater()
    qapp.processEvents()


def test_main_window_password_unlock_paths(qapp, database, theme_manager, monkeypatch):
    window = MainWindow(database, theme_manager)
    window.password_service.set_password("correct")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    class CanceledUnlock:
        def __init__(self, *args):
            pass

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(main_window_module, "PasswordUnlockDialog", CanceledUnlock)
    assert window._password_entry_allowed() is False
    assert window.welcome_page.enter_button.isEnabled() is True
    window._handle_welcome_entry()
    assert window.shell_stack.currentIndex() == 0

    class WrongUnlock:
        def __init__(self, *args):
            pass

        def exec(self):
            return QDialog.Accepted

        def password(self):
            return "wrong"

    monkeypatch.setattr(main_window_module, "PasswordUnlockDialog", WrongUnlock)
    assert window._password_entry_allowed() is False
    assert warnings

    class CorrectUnlock(WrongUnlock):
        def password(self):
            return "correct"

    monkeypatch.setattr(main_window_module, "PasswordUnlockDialog", CorrectUnlock)
    assert window._password_entry_allowed() is True
    window._handle_welcome_entry()
    assert window.shell_stack.currentIndex() == 1
    window.close()
    window.deleteLater()
    qapp.processEvents()
