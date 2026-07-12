from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QTabWidget, QWidget
from shiboken6 import isValid

from ordocor.ui.design_config import ANIMATION


class FadeMixin:
    def _fade_in_widget(self, widget: QWidget | None, duration_ms: int | None = None) -> None:
        if widget is None:
            return

        self._stop_active_fade_animation()

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(ANIMATION["opacity_start"])
        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(duration_ms if duration_ms is not None else ANIMATION["page_fade_ms"])
        animation.setStartValue(ANIMATION["opacity_start"])
        animation.setEndValue(ANIMATION["opacity_end"])
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def clear_effect() -> None:
            if self._active_fade_animation is animation:
                self._active_fade_animation = None
            if _qt_object_is_valid(widget) and _qt_object_is_valid(effect):
                if widget.graphicsEffect() is effect:
                    widget.setGraphicsEffect(None)
            if _qt_object_is_valid(effect):
                effect.deleteLater()

        animation.finished.connect(clear_effect)
        widget.destroyed.connect(animation.stop)
        effect.destroyed.connect(animation.stop)

        self._active_fade_animation = animation
        animation.start()

    def _stop_active_fade_animation(self) -> None:
        animation = getattr(self, "_active_fade_animation", None)
        if animation is not None and _qt_object_is_valid(animation):
            animation.stop()
        self._active_fade_animation = None


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


def _qt_object_is_valid(obj: object) -> bool:
    try:
        return isValid(obj)
    except RuntimeError:
        return False
