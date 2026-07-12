from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


ACCOUNT_ID_ROLE = Qt.UserRole + 6


class AccountDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        account: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.institution_input = QLineEdit(str(account.get("institution", "")) if account else "")
        self.institution_input.setPlaceholderText("Example: Fidelity")

        self.name_input = QLineEdit(str(account.get("name", "")) if account else "")
        self.name_input.setPlaceholderText("Example: Roth IRA")

        self.type_input = QComboBox()
        self.type_input.addItems(("Brokerage", "Savings", "Checking", "Credit"))
        if account and account.get("account_type"):
            index = self.type_input.findText(str(account["account_type"]).title())
            if index >= 0:
                self.type_input.setCurrentIndex(index)

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Institution"), 0, 0)
        form.addWidget(self.institution_input, 0, 1)
        form.addWidget(QLabel("Account Name"), 1, 0)
        form.addWidget(self.name_input, 1, 1)
        form.addWidget(QLabel("Account Type"), 2, 0)
        form.addWidget(self.type_input, 2, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def account_data(self) -> dict[str, object]:
        return {
            "institution": self.institution_input.text().strip(),
            "name": self.name_input.text().strip(),
            "account_type": self.type_input.currentText().lower(),
        }


class AccountsMixin:
    def _accounts_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Accounts")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_account)
        modify_button.clicked.connect(self._modify_account)
        remove_button.clicked.connect(self._remove_account)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.accounts_table = QTableWidget(0, 3)
        self.accounts_table.setHorizontalHeaderLabels(("Institution", "Account Name", "Type"))
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.doubleClicked.connect(self._modify_account)

        layout.addLayout(header)
        layout.addWidget(self.accounts_table, stretch=1)
        self._load_accounts()
        return page

    def _load_accounts(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, institution, name, account_type
                    FROM investment_accounts
                    ORDER BY institution, name, id
                    """
            ).fetchall()

        self.accounts_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.accounts_table.insertRow(row_index)
            values = (
                row["institution"] or "",
                row["name"] or "",
                str(row["account_type"] or "").title(),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(ACCOUNT_ID_ROLE, row["id"])
                self.accounts_table.setItem(row_index, column, item)

    def _add_account(self) -> None:
        dialog = AccountDialog(self, "Add Account")
        if dialog.exec() != QDialog.Accepted:
            return

        account = dialog.account_data()
        if not self._validate_account(account):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    INSERT INTO investment_accounts (institution, name, account_type)
                    VALUES (?, ?, ?)
                    """,
                (account["institution"], account["name"], account["account_type"]),
            )
        self._load_accounts()

    def _modify_account(self) -> None:
        account_id = self._selected_account_id()
        if account_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT id, institution, name, account_type
                    FROM investment_accounts
                    WHERE id = ?
                    """,
                (account_id,),
            ).fetchone()

        if row is None:
            return

        dialog = AccountDialog(self, "Modify Account", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        account = dialog.account_data()
        if not self._validate_account(account):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE investment_accounts
                    SET institution = ?,
                        name = ?,
                        account_type = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (
                    account["institution"],
                    account["name"],
                    account["account_type"],
                    account_id,
                ),
            )
        self._load_accounts()

    def _remove_account(self) -> None:
        account_id = self._selected_account_id()
        if account_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM investment_accounts WHERE id = ?", (account_id,))
        self._load_accounts()

    def _selected_account_id(self) -> int | None:
        selected_items = self.accounts_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.accounts_table.item(row, 0)
        return item.data(ACCOUNT_ID_ROLE) if item else None

    def _validate_account(self, account: dict[str, object]) -> bool:
        if not account["institution"] or not account["name"]:
            QMessageBox.warning(
                self,
                "Missing Account Details",
                "Institution and account name are required.",
            )
            return False
        return True
