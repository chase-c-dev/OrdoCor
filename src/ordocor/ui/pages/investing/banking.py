from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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


BANKING_PRODUCT_ID_ROLE = Qt.UserRole + 3


class CertificateOfDepositDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        cd: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.name_input = QLineEdit(str(cd.get("product_name", "")) if cd else "")
        self.name_input.setPlaceholderText("Example: 12 Month CD")

        self.bank_input = QLineEdit(str(cd.get("institution", "")) if cd else "")
        self.bank_input.setPlaceholderText("Example: Local Bank")

        self.open_date_input = QDateEdit()
        self.open_date_input.setCalendarPopup(True)
        self.open_date_input.setDisplayFormat("yyyy-MM-dd")
        if cd and cd.get("open_date"):
            self.open_date_input.setDate(QDate.fromString(str(cd["open_date"]), "yyyy-MM-dd"))

        self.principal_input = self._money_input(cd, "principal")
        self.interest_rate_input = QDoubleSpinBox()
        self.interest_rate_input.setRange(0, 100)
        self.interest_rate_input.setDecimals(3)
        self.interest_rate_input.setSuffix("%")
        self.interest_rate_input.setValue(float(cd.get("interest_rate", 0) or 0) if cd else 0)

        self.maturity_date_input = QDateEdit()
        self.maturity_date_input.setCalendarPopup(True)
        self.maturity_date_input.setDisplayFormat("yyyy-MM-dd")
        if cd and cd.get("maturity_date"):
            self.maturity_date_input.setDate(
                QDate.fromString(str(cd["maturity_date"]), "yyyy-MM-dd")
            )

        self.maturity_value_input = self._money_input(cd, "maturity_value")

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("CD Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Bank"), 1, 0)
        form.addWidget(self.bank_input, 1, 1)
        form.addWidget(QLabel("Open Date"), 2, 0)
        form.addWidget(self.open_date_input, 2, 1)
        form.addWidget(QLabel("Principal"), 3, 0)
        form.addWidget(self.principal_input, 3, 1)
        form.addWidget(QLabel("Interest Rate"), 4, 0)
        form.addWidget(self.interest_rate_input, 4, 1)
        form.addWidget(QLabel("Maturity Date"), 5, 0)
        form.addWidget(self.maturity_date_input, 5, 1)
        form.addWidget(QLabel("Maturity Value"), 6, 0)
        form.addWidget(self.maturity_value_input, 6, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def cd_data(self) -> dict[str, object]:
        return {
            "product_name": self.name_input.text().strip(),
            "institution": self.bank_input.text().strip(),
            "open_date": self.open_date_input.date().toString("yyyy-MM-dd"),
            "principal": self.principal_input.value(),
            "interest_rate": self.interest_rate_input.value(),
            "maturity_date": self.maturity_date_input.date().toString("yyyy-MM-dd"),
            "maturity_value": self.maturity_value_input.value(),
        }

    def _money_input(self, cd: dict[str, object] | None, key: str) -> QDoubleSpinBox:
        input_widget = QDoubleSpinBox()
        input_widget.setRange(0, 1_000_000_000)
        input_widget.setDecimals(2)
        input_widget.setPrefix("$")
        input_widget.setValue(float(cd.get(key, 0) or 0) if cd else 0)
        return input_widget


class BankingMixin:
    def _banking_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Certificates of Deposit")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_cd)
        modify_button.clicked.connect(self._modify_cd)
        remove_button.clicked.connect(self._remove_cd)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.banking_table = QTableWidget(0, 7)
        self.banking_table.setHorizontalHeaderLabels(
            (
                "CD Name",
                "Bank",
                "Open Date",
                "Principal",
                "Rate",
                "Maturity Date",
                "Maturity Value",
            )
        )
        self.banking_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.banking_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.banking_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.banking_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.banking_table.verticalHeader().setVisible(False)
        self.banking_table.doubleClicked.connect(self._modify_cd)

        layout.addLayout(header)
        layout.addWidget(self.banking_table, stretch=1)
        self._load_cds()
        return page

    def _load_cds(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, product_name, institution, open_date, principal,
                           interest_rate, maturity_date, maturity_value
                    FROM investment_banking_products
                    ORDER BY maturity_date, institution, product_name, id
                    """
            ).fetchall()

        self.banking_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.banking_table.insertRow(row_index)
            values = (
                row["product_name"] or "",
                row["institution"] or "",
                row["open_date"] or "",
                self._money(row["principal"]),
                self._percent(row["interest_rate"]),
                row["maturity_date"] or "",
                self._money(row["maturity_value"]),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(BANKING_PRODUCT_ID_ROLE, row["id"])
                self.banking_table.setItem(row_index, column, item)

    def _add_cd(self) -> None:
        dialog = CertificateOfDepositDialog(self, "Add Certificate of Deposit")
        if dialog.exec() != QDialog.Accepted:
            return

        cd = dialog.cd_data()
        if not self._validate_cd(cd):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    INSERT INTO investment_banking_products (
                        product_name, institution, open_date, principal,
                        interest_rate, maturity_date, maturity_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                (
                    cd["product_name"],
                    cd["institution"],
                    cd["open_date"],
                    cd["principal"],
                    cd["interest_rate"],
                    cd["maturity_date"],
                    cd["maturity_value"],
                ),
            )
        self._load_cds()

    def _modify_cd(self) -> None:
        cd_id = self._selected_cd_id()
        if cd_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT id, product_name, institution, open_date, principal,
                           interest_rate, maturity_date, maturity_value
                    FROM investment_banking_products
                    WHERE id = ?
                    """,
                (cd_id,),
            ).fetchone()

        if row is None:
            return

        dialog = CertificateOfDepositDialog(self, "Modify Certificate of Deposit", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        cd = dialog.cd_data()
        if not self._validate_cd(cd):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE investment_banking_products
                    SET product_name = ?,
                        institution = ?,
                        open_date = ?,
                        principal = ?,
                        interest_rate = ?,
                        maturity_date = ?,
                        maturity_value = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (
                    cd["product_name"],
                    cd["institution"],
                    cd["open_date"],
                    cd["principal"],
                    cd["interest_rate"],
                    cd["maturity_date"],
                    cd["maturity_value"],
                    cd_id,
                ),
            )
        self._load_cds()

    def _remove_cd(self) -> None:
        cd_id = self._selected_cd_id()
        if cd_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM investment_banking_products WHERE id = ?", (cd_id,))
        self._load_cds()

    def _selected_cd_id(self) -> int | None:
        selected_items = self.banking_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.banking_table.item(row, 0)
        return item.data(BANKING_PRODUCT_ID_ROLE) if item else None

    def _validate_cd(self, cd: dict[str, object]) -> bool:
        if not cd["product_name"] or not cd["institution"]:
            QMessageBox.warning(self, "Missing CD Details", "CD name and bank are required.")
            return False
        return True
