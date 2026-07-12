from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QIntValidator, QTextCharFormat
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ordocor.ui.theme.stylesheet import theme_color


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    field_type: str = "text"


class PropertyFormDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        fields: tuple[FieldSpec, ...],
        data: dict[str, object] | None = None,
    ) -> None:
        super().__init__(parent)
        self.fields = fields
        self.inputs: dict[str, QWidget] = {}
        self.setWindowTitle(title)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        form = QGridLayout()
        form.setSpacing(10)
        for row, field in enumerate(fields):
            input_widget = self._input_for(field, data or {})
            self.inputs[field.key] = input_widget
            form.addWidget(QLabel(field.label), row, 0)
            form.addWidget(input_widget, row, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def form_data(self) -> dict[str, object]:
        return {field.key: self._value_for(field) for field in self.fields}

    def _input_for(self, field: FieldSpec, data: dict[str, object]) -> QWidget:
        value = data.get(field.key, "")
        if field.field_type == "money":
            widget = QDoubleSpinBox()
            widget.setRange(0, 1_000_000_000)
            widget.setDecimals(2)
            widget.setPrefix("$")
            widget.setValue(float(value or 0))
            return widget
        if field.field_type == "number":
            widget = QSpinBox()
            widget.setRange(0, 9999)
            widget.setValue(int(value or 0))
            return widget
        if field.field_type == "integer_text":
            widget = QLineEdit(str(value or ""))
            widget.setValidator(QIntValidator(0, 9999, widget))
            return widget
        if field.field_type == "date":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd")
            _style_calendar_popup(widget)
            if value:
                widget.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))
            return widget
        if field.field_type == "multiline":
            widget = QTextEdit(str(value or ""))
            widget.setMaximumHeight(120)
            return widget
        return QLineEdit(str(value or ""))

    def _value_for(self, field: FieldSpec) -> object:
        widget = self.inputs[field.key]
        if field.field_type == "money":
            return widget.value()
        if field.field_type == "number":
            return widget.value()
        if field.field_type == "integer_text":
            text = widget.text().strip()
            return int(text) if text else None
        if field.field_type == "date":
            return widget.date().toString("yyyy-MM-dd")
        if field.field_type == "multiline":
            return widget.toPlainText().strip()
        return widget.text().strip()


def _style_calendar_popup(widget: QDateEdit) -> None:
    calendar = widget.calendarWidget()
    text_format = QTextCharFormat()
    text_format.setForeground(QColor(theme_color("bright_text")))
    for day in (
        Qt.Monday,
        Qt.Tuesday,
        Qt.Wednesday,
        Qt.Thursday,
        Qt.Friday,
        Qt.Saturday,
        Qt.Sunday,
    ):
        calendar.setWeekdayTextFormat(day, text_format)
