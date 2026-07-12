from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextListFormat
from PySide6.QtWidgets import (
    QComboBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


INVESTMENT_PLAN_ID_ROLE = Qt.UserRole + 5


class InvestmentPlanDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        plan: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(620, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.name_input = QLineEdit(str(plan.get("idea_name", "")) if plan else "")
        self.name_input.setPlaceholderText("Example: Apple Inc. or Vanguard 500 Index Fund")

        self.type_input = QComboBox()
        self.type_input.addItems(("Stock", "Mutual Fund"))
        if plan and plan.get("investment_type"):
            index = self.type_input.findText(str(plan["investment_type"]))
            if index >= 0:
                self.type_input.setCurrentIndex(index)

        self.desired_price_input = QDoubleSpinBox()
        self.desired_price_input.setRange(0, 1_000_000_000)
        self.desired_price_input.setDecimals(2)
        self.desired_price_input.setPrefix("$")
        self.desired_price_input.setValue(
            float(plan.get("desired_purchase_price", 0) or 0) if plan else 0
        )

        self.shares_input = QDoubleSpinBox()
        self.shares_input.setRange(0, 1_000_000_000)
        self.shares_input.setDecimals(6)
        self.shares_input.setValue(float(plan.get("desired_shares", 0) or 0) if plan else 0)

        form = QGridLayout()
        form.setSpacing(10)
        form.addWidget(QLabel("Investment Name"), 0, 0)
        form.addWidget(self.name_input, 0, 1)
        form.addWidget(QLabel("Type"), 1, 0)
        form.addWidget(self.type_input, 1, 1)
        form.addWidget(QLabel("Desired Share Price"), 2, 0)
        form.addWidget(self.desired_price_input, 2, 1)
        form.addWidget(QLabel("Desired Shares"), 3, 0)
        form.addWidget(self.shares_input, 3, 1)

        notes_label = QLabel("Detailed Notes")
        notes_label.setStyleSheet("color: #F3E7C9; font-weight: 800;")

        note_actions = QHBoxLayout()
        bold_button = QPushButton("B")
        italic_button = QPushButton("I")
        underline_button = QPushButton("U")
        bullet_button = QPushButton("Bullets")
        bold_button.clicked.connect(self._toggle_bold)
        italic_button.clicked.connect(self._toggle_italic)
        underline_button.clicked.connect(self._toggle_underline)
        bullet_button.clicked.connect(self._insert_bullets)
        note_actions.addWidget(bold_button)
        note_actions.addWidget(italic_button)
        note_actions.addWidget(underline_button)
        note_actions.addWidget(bullet_button)
        note_actions.addStretch()

        self.notes_input = QTextEdit()
        self.notes_input.setAcceptRichText(True)
        self.notes_input.setHtml(str(plan.get("notes", "")) if plan else "")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(notes_label)
        layout.addLayout(note_actions)
        layout.addWidget(self.notes_input, stretch=1)
        layout.addWidget(buttons)

    def plan_data(self) -> dict[str, object]:
        return {
            "idea_name": self.name_input.text().strip(),
            "investment_type": self.type_input.currentText(),
            "desired_purchase_price": self.desired_price_input.value(),
            "desired_shares": self.shares_input.value(),
            "notes": self.notes_input.toHtml(),
        }

    def _toggle_bold(self) -> None:
        weight = 400 if self.notes_input.fontWeight() > 400 else 700
        self.notes_input.setFontWeight(weight)

    def _toggle_italic(self) -> None:
        self.notes_input.setFontItalic(not self.notes_input.fontItalic())

    def _toggle_underline(self) -> None:
        self.notes_input.setFontUnderline(not self.notes_input.fontUnderline())

    def _insert_bullets(self) -> None:
        self.notes_input.textCursor().insertList(QTextListFormat.ListDisc)


class InvestmentPlansMixin:
    def _investment_plans_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Investment Plans")
        title.setStyleSheet("color: #F3E7C9; font-size: 20px; font-weight: 800;")
        add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self._add_investment_plan)
        modify_button.clicked.connect(self._modify_investment_plan)
        remove_button.clicked.connect(self._remove_investment_plan)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(modify_button)
        header.addWidget(remove_button)

        self.investment_plans_table = QTableWidget(0, 5)
        self.investment_plans_table.setHorizontalHeaderLabels(
            (
                "Investment",
                "Type",
                "Desired Price",
                "Desired Shares",
                "Planned Amount",
            )
        )
        self.investment_plans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.investment_plans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.investment_plans_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.investment_plans_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.investment_plans_table.verticalHeader().setVisible(False)
        self.investment_plans_table.doubleClicked.connect(self._modify_investment_plan)

        hint = QLabel("Double-click a plan to open the expanded notes view.")
        hint.setStyleSheet("color: #B6A896; font-size: 12px;")

        layout.addLayout(header)
        layout.addWidget(hint)
        layout.addWidget(self.investment_plans_table, stretch=1)
        self._load_investment_plans()
        return page

    def _load_investment_plans(self) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                    SELECT id, idea_name, investment_type, desired_purchase_price, desired_shares
                    FROM investment_pipeline
                    ORDER BY investment_type, idea_name, id
                    """
            ).fetchall()

        self.investment_plans_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.investment_plans_table.insertRow(row_index)
            planned_amount = float(row["desired_purchase_price"] or 0) * float(
                row["desired_shares"] or 0
            )
            values = (
                row["idea_name"] or "",
                row["investment_type"] or "",
                self._money(row["desired_purchase_price"]),
                self._number(row["desired_shares"]),
                self._money(planned_amount),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(INVESTMENT_PLAN_ID_ROLE, row["id"])
                self.investment_plans_table.setItem(row_index, column, item)

    def _add_investment_plan(self) -> None:
        dialog = InvestmentPlanDialog(self, "Add Investment Plan")
        if dialog.exec() != QDialog.Accepted:
            return

        plan = dialog.plan_data()
        if not self._validate_investment_plan(plan):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    INSERT INTO investment_pipeline (
                        idea_name, investment_type, desired_purchase_price, desired_shares, notes
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                (
                    plan["idea_name"],
                    plan["investment_type"],
                    plan["desired_purchase_price"],
                    plan["desired_shares"],
                    plan["notes"],
                ),
            )
        self._load_investment_plans()

    def _modify_investment_plan(self) -> None:
        plan_id = self._selected_investment_plan_id()
        if plan_id is None:
            return

        with self.database.connect() as connection:
            row = connection.execute(
                """
                    SELECT id, idea_name, investment_type, desired_purchase_price, desired_shares, notes
                    FROM investment_pipeline
                    WHERE id = ?
                    """,
                (plan_id,),
            ).fetchone()

        if row is None:
            return

        dialog = InvestmentPlanDialog(self, "Modify Investment Plan", dict(row))
        if dialog.exec() != QDialog.Accepted:
            return

        plan = dialog.plan_data()
        if not self._validate_investment_plan(plan):
            return

        with self.database.connect() as connection:
            connection.execute(
                """
                    UPDATE investment_pipeline
                    SET idea_name = ?,
                        investment_type = ?,
                        desired_purchase_price = ?,
                        desired_shares = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                (
                    plan["idea_name"],
                    plan["investment_type"],
                    plan["desired_purchase_price"],
                    plan["desired_shares"],
                    plan["notes"],
                    plan_id,
                ),
            )
        self._load_investment_plans()

    def _remove_investment_plan(self) -> None:
        plan_id = self._selected_investment_plan_id()
        if plan_id is None:
            return

        with self.database.connect() as connection:
            connection.execute("DELETE FROM investment_pipeline WHERE id = ?", (plan_id,))
        self._load_investment_plans()

    def _selected_investment_plan_id(self) -> int | None:
        selected_items = self.investment_plans_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.investment_plans_table.item(row, 0)
        return item.data(INVESTMENT_PLAN_ID_ROLE) if item else None

    def _validate_investment_plan(self, plan: dict[str, object]) -> bool:
        if not plan["idea_name"]:
            QMessageBox.warning(self, "Missing Investment Plan", "Investment name is required.")
            return False
        return True
