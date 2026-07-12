from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ordocor.data.database import Database
from ordocor.ui.animated_widgets import AnimatedTabWidget

from .accounts import AccountsMixin
from .stocks import StocksMixin
from .mutual_funds import MutualFundsMixin
from .banking import BankingMixin
from .collectibles import CollectiblesMixin
from .plans import InvestmentPlansMixin


class InvestingPage(
    AccountsMixin,
    StocksMixin,
    MutualFundsMixin,
    BankingMixin,
    CollectiblesMixin,
    InvestmentPlansMixin,
    QWidget,
):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        heading = QLabel("Investing")
        heading.setStyleSheet("color: #F3E7C9; font-size: 28px; font-weight: 800;")

        self.tabs = AnimatedTabWidget()
        self.tabs.addTab(self._accounts_page(), "Accounts")
        self.tabs.addTab(self._stocks_page(), "Stocks")
        self.tabs.addTab(self._mutual_funds_page(), "Mutual Funds")
        self.tabs.addTab(self._banking_page(), "Banking")
        self.tabs.addTab(self._collectibles_wishlist_page(), "Collectibles")
        self.tabs.addTab(
            self._investment_plans_page(),
            "Investment Plans",
        )
        self.tabs.currentChanged.connect(self._refresh_active_market_data)

        layout.addWidget(heading)
        layout.addWidget(self.tabs, stretch=1)

    def _refresh_active_market_data(self, tab_index: int) -> None:
        if tab_index == 1:
            self._refresh_market_data()
        elif tab_index == 2:
            self._refresh_mutual_fund_market_data()

    def _money(self, value: object) -> str:
        return f"${float(value or 0):,.2f}"

    def _percent(self, value: object) -> str:
        formatted = f"{float(value or 0):.3f}".rstrip("0").rstrip(".")
        return f"{formatted}%"

    def _number(self, value: object) -> str:
        return f"{float(value or 0):,.6f}".rstrip("0").rstrip(".")

    def _optional_money(self, value: object, signed: bool = False) -> str:
        if value is None:
            return "-"
        amount = float(value)
        if not signed:
            return self._money(amount)
        prefix = "+" if amount > 0 else "-" if amount < 0 else ""
        return f"{prefix}${abs(amount):,.2f}"

    def _optional_percent(self, value: object, signed: bool = False) -> str:
        if value is None:
            return "-"
        prefix = "+" if signed and float(value) > 0 else ""
        return f"{prefix}{self._percent(value)}"
