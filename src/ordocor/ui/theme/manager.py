from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QPushButton, QWidget

from ordocor.data.database import Database
from ordocor.ui.design_config import ANIMATION

from .palettes import BASE_THEME, DEFAULT_THEME, PALETTES
from .stylesheet import set_active_theme, stylesheet_for


class ThemeManager(QObject):
    def __init__(self, database: Database, app: QApplication) -> None:
        super().__init__(app)
        self.database = database
        self.app = app
        self._button_animations: dict[QPushButton, QPropertyAnimation] = {}
        self.current_theme = self._load_theme()
        set_active_theme(self.current_theme)
        self.app.setStyleSheet(stylesheet_for(self.current_theme))
        self.app.installEventFilter(self)

    @property
    def theme_names(self) -> tuple[str, ...]:
        return tuple(PALETTES)

    def apply(self, theme_name: str, persist: bool = True) -> None:
        if theme_name not in PALETTES:
            return

        previous_theme = self.current_theme
        self.current_theme = theme_name
        set_active_theme(theme_name)
        self.app.setStyleSheet(stylesheet_for(theme_name))

        for widget in self.app.topLevelWidgets():
            self._retheme_widget_tree(widget, previous_theme, theme_name)

        if persist:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO app_settings (key, value)
                    VALUES ('color_theme', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (theme_name,),
                )

    def refresh_widget(self, root: QWidget) -> None:
        self._retheme_widget_tree(root, BASE_THEME, self.current_theme)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QWidget):
            if event.type() == QEvent.Polish:
                self._retheme_widget(watched, BASE_THEME, self.current_theme)
                self._prepare_button_feedback(watched)
            elif event.type() == QEvent.Show and watched.isWindow():
                self._retheme_widget_tree(watched, BASE_THEME, self.current_theme)
        return super().eventFilter(watched, event)

    def _load_theme(self) -> str:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = 'color_theme'"
            ).fetchone()
        if row and row["value"] in PALETTES:
            return row["value"]
        return DEFAULT_THEME

    def _retheme_widget_tree(
        self,
        root: QWidget,
        source_theme: str,
        target_theme: str,
    ) -> None:
        for widget in (root, *root.findChildren(QWidget)):
            self._retheme_widget(widget, source_theme, target_theme)
            self._prepare_button_feedback(widget)

    def _retheme_widget(
        self,
        widget: QWidget,
        source_theme: str,
        target_theme: str,
    ) -> None:
        style = widget.styleSheet()
        if not style:
            return

        themed_style = _replace_palette(style, source_theme, target_theme)
        if themed_style != style:
            widget.setStyleSheet(themed_style)

    def _prepare_button_feedback(self, widget: QWidget) -> None:
        if not isinstance(widget, QPushButton):
            return
        if widget.property("ordocor_button_feedback_connected"):
            return
        widget.setProperty("ordocor_button_feedback_connected", True)
        widget.clicked.connect(lambda _checked=False, button=widget: self._animate_button(button))

    def _animate_button(self, button: QPushButton) -> None:
        if not button.isEnabled():
            return

        effect = QGraphicsOpacityEffect(button)
        effect.setOpacity(ANIMATION["button_feedback_opacity_start"])
        button.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", button)
        animation.setDuration(ANIMATION["button_feedback_ms"])
        animation.setStartValue(ANIMATION["button_feedback_opacity_start"])
        animation.setEndValue(ANIMATION["opacity_end"])
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: self._clear_button_animation(button, effect))
        self._button_animations[button] = animation
        animation.start()

    def _clear_button_animation(
        self,
        button: QPushButton,
        effect: QGraphicsOpacityEffect,
    ) -> None:
        if button.graphicsEffect() is effect:
            button.setGraphicsEffect(None)
        self._button_animations.pop(button, None)


def _replace_palette(text: str, source_theme: str, target_theme: str) -> str:
    source = PALETTES[source_theme]
    target = PALETTES[target_theme]
    for token, source_color in source.items():
        text = text.replace(source_color, target[token])
    return text
