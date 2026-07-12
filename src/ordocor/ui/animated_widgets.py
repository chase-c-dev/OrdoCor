from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QTabWidget, QWidget

from ordocor.ui.design_config import ANIMATION


class FadeMixin:
    def _fade_in_widget(self, widget: QWidget | None, duration_ms: int | None = None) -> None:
        if widget is None:
            return

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(ANIMATION["opacity_start"])
        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration_ms if duration_ms is not None else ANIMATION["page_fade_ms"])
        animation.setStartValue(ANIMATION["opacity_start"])
        animation.setEndValue(ANIMATION["opacity_end"])
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: widget.setGraphicsEffect(None))

        self._active_fade_animation = animation
        animation.start()


class AnimatedStackedWidget(FadeMixin, QStackedWidget):
    def __init__(self, parent: QWidget | None = None, duration_ms: int | None = None) -> None:
        super().__init__(parent)
        self._fade_duration_ms = duration_ms
        self._active_fade_animation: QPropertyAnimation | None = None

    def setCurrentIndex(self, index: int) -> None:
        if index == self.currentIndex() or not 0 <= index < self.count():
            return

        super().setCurrentIndex(index)
        self._fade_in_widget(self.currentWidget(), self._fade_duration_ms)


class AnimatedTabWidget(FadeMixin, QTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active_fade_animation: QPropertyAnimation | None = None
        self.currentChanged.connect(lambda _index: self._fade_in_widget(self.currentWidget()))
