from dataclasses import dataclass

from PySide6.QtCore import Qt


TODO_ID_ROLE = Qt.UserRole + 1
CALENDAR_ITEM_ID_ROLE = Qt.UserRole + 2
UPCOMING_DATE_ROLE = Qt.UserRole + 3


@dataclass(frozen=True)
class CalendarItem:
    id: int | None
    title: str
    notes: str
