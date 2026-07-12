from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PasswordSetupDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Protect OrdoCor")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        description = QLabel(
            "You can add an OrdoCor password for this app, or skip this and keep opening "
            "OrdoCor without a password."
        )
        description.setWordWrap(True)

        form = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        form.addRow("Password", self.password_input)
        form.addRow("Confirm Password", self.confirm_input)

        buttons = QDialogButtonBox()
        self.use_password_button = QPushButton("Use Password")
        self.skip_button = QPushButton("Skip")
        buttons.addButton(self.use_password_button, QDialogButtonBox.AcceptRole)
        buttons.addButton(self.skip_button, QDialogButtonBox.RejectRole)
        self.use_password_button.clicked.connect(self._accept_password)
        self.skip_button.clicked.connect(self.reject)

        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self.password_input.text()

    def _accept_password(self) -> None:
        if not self.password_input.text():
            QMessageBox.warning(self, "Password Required", "Enter a password or choose Skip.")
            return
        if self.password_input.text() != self.confirm_input.text():
            QMessageBox.warning(self, "Passwords Do Not Match", "Enter the same password twice.")
            return
        self.accept()


class PasswordUnlockDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Unlock OrdoCor")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        description = QLabel("Enter your OrdoCor password to continue.")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.accept)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(description)
        layout.addWidget(self.password_input)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self.password_input.text()


class PasswordChangeDialog(QDialog):
    def __init__(self, require_current: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.require_current = require_current
        self.setWindowTitle("OrdoCor Password")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        form = QFormLayout()
        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.Password)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        if require_current:
            form.addRow("Current Password", self.current_input)
        form.addRow("New Password", self.password_input)
        form.addRow("Confirm Password", self.confirm_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_password)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def current_password(self) -> str:
        return self.current_input.text()

    def password(self) -> str:
        return self.password_input.text()

    def _accept_password(self) -> None:
        if self.require_current and not self.current_input.text():
            QMessageBox.warning(self, "Current Password Required", "Enter your current password.")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Password Required", "Enter a new password.")
            return
        if self.password_input.text() != self.confirm_input.text():
            QMessageBox.warning(self, "Passwords Do Not Match", "Enter the same password twice.")
            return
        self.accept()


class PasswordConfirmDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Disable Password")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        description = QLabel("Enter your current password to disable OrdoCor password protection.")
        description.setWordWrap(True)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.accept)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(description)
        layout.addWidget(self.password_input)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self.password_input.text()
