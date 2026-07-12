from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


def configure_compact_market_table(table: QTableWidget, headers: tuple[str, ...]) -> None:
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setWordWrap(False)
    table.verticalHeader().setVisible(False)
    table.setStyleSheet(
        """
        QHeaderView::section {
            font-size: 11px;
            padding: 3px;
        }
        """
    )

    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setMinimumSectionSize(48)
    header.setDefaultAlignment(Qt.AlignCenter)
    header.setFixedHeight(44)

    for column, label in enumerate(headers):
        item = QTableWidgetItem(label)
        item.setTextAlignment(Qt.AlignCenter)
        item.setToolTip(label.replace("\n", " "))
        table.setHorizontalHeaderItem(column, item)
