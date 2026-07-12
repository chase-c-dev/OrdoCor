from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QRectF,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ordocor.ui.design_config import ANIMATION
from ordocor.ui.theme import themed_stylesheet


class LockIcon(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._unlock_progress = 0.0
        self.setFixedSize(38, 38)

    def unlock_progress(self) -> float:
        return self._unlock_progress

    def set_unlock_progress(self, value: float) -> None:
        self._unlock_progress = max(0.0, min(1.0, value))
        self.update()

    unlockProgress = Property(float, unlock_progress, set_unlock_progress)

    def reset_locked(self) -> None:
        self.set_unlock_progress(0.0)

    def set_unlocked(self) -> None:
        self.set_unlock_progress(1.0)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        accent = QColor(themed_stylesheet("#C0A361"))
        body_fill = QColor(themed_stylesheet("#44363B"))
        body_border = QColor(themed_stylesheet("#F3E7C9"))

        body = QRectF(8, 18, 22, 15)
        painter.setPen(QPen(body_border, 2))
        painter.setBrush(body_fill)
        painter.drawRoundedRect(body, 4, 4)

        keyhole = QPainterPath()
        keyhole.addEllipse(QRectF(17, 23, 4, 4))
        keyhole.addRoundedRect(QRectF(18, 26, 2, 4), 1, 1)
        painter.fillPath(keyhole, accent)

        progress = self._unlock_progress
        shackle_offset = 7 * progress
        shackle_lift = -4 * progress
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(accent, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        shackle = QPainterPath()
        shackle.moveTo(12 + shackle_offset, 19 + shackle_lift)
        shackle.lineTo(12 + shackle_offset, 15 + shackle_lift)
        shackle.cubicTo(
            12 + shackle_offset,
            6 + shackle_lift,
            26 + shackle_offset,
            6 + shackle_lift,
            26 + shackle_offset,
            15 + shackle_lift,
        )
        shackle.lineTo(26 + shackle_offset, 17 + shackle_lift + (5 * progress))
        painter.drawPath(shackle)


class WelcomePage(QWidget):
    enter_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._intro_animation: QPropertyAnimation | None = None
        self._unlock_animation: QPropertyAnimation | None = None
        self._intro_started = False
        self.setObjectName("welcomePage")
        self.setStyleSheet(
            """
            QWidget#welcomePage {
                background: #191518;
            }
            QWidget#welcomePanel {
                background: #231C20;
                border: 1px solid #665451;
                border-radius: 10px;
            }
            QWidget#welcomeLockBadge {
                background: #33292D;
                border: 1px solid #C0A361;
                border-radius: 32px;
            }
            QLabel#welcomeTitle {
                color: #F3E7C9;
                font-size: 34px;
                font-weight: 800;
            }
            QLabel#welcomeSubtitle {
                color: #C7B99F;
                font-size: 15px;
            }
            QLabel#welcomeCaption,
            QLabel#welcomeStatus {
                color: #9B8F83;
                font-size: 12px;
                font-weight: 700;
            }
            """
        )

        self.panel = QWidget(self)
        self.panel.setObjectName("welcomePanel")
        self.panel.setFixedSize(560, 360)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(36, 34, 36, 34)
        panel_layout.setSpacing(16)

        badge_row = QHBoxLayout()
        badge_row.addStretch()
        lock_badge = QWidget()
        lock_badge.setObjectName("welcomeLockBadge")
        lock_badge.setFixedSize(64, 64)
        lock_layout = QVBoxLayout(lock_badge)
        lock_layout.setContentsMargins(0, 0, 0, 0)
        self.lock_icon = LockIcon()
        lock_layout.addWidget(self.lock_icon, alignment=Qt.AlignCenter)
        badge_row.addWidget(lock_badge)
        badge_row.addStretch()

        caption = QLabel("PRIVATE LOCAL WORKSPACE")
        caption.setObjectName("welcomeCaption")
        caption.setAlignment(Qt.AlignCenter)

        title = QLabel("Welcome To OrdoCor")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(
            "Your life management dashboard is ready. Unlock the workspace to continue."
        )
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        self.status_label = QLabel("Stored locally on this computer.")
        self.status_label.setObjectName("welcomeStatus")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.enter_button = QPushButton("Enter")
        self.enter_button.setMinimumWidth(150)
        self.enter_button.clicked.connect(self.unlock)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.enter_button)
        button_row.addStretch()

        panel_layout.addLayout(badge_row)
        panel_layout.addWidget(caption)
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)
        panel_layout.addWidget(self.status_label)
        panel_layout.addStretch()
        panel_layout.addLayout(button_row)
        self._place_panel_at_start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._intro_started:
            self._intro_started = True
            QTimer.singleShot(0, self.start_intro_animation)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._intro_animation is None:
            self.panel.move(self._final_panel_pos())

    def start_intro_animation(self) -> None:
        self.panel.move(self._start_panel_pos())
        animation = QPropertyAnimation(self.panel, b"pos", self)
        animation.setDuration(ANIMATION["welcome_slide_ms"])
        animation.setStartValue(self._start_panel_pos())
        animation.setEndValue(self._final_panel_pos())
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(self._finish_intro_animation)
        self._intro_animation = animation
        animation.start()

    def unlock(self) -> None:
        if self._unlock_animation is not None:
            return

        self.enter_button.setEnabled(False)
        self.status_label.setText("Unlocking OrdoCor...")
        self.lock_icon.reset_locked()

        animation = QPropertyAnimation(self.lock_icon, b"unlockProgress", self.lock_icon)
        animation.setDuration(ANIMATION["welcome_unlock_ms"])
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(self._finish_unlock)
        self._unlock_animation = animation
        animation.start()

    def reset_after_denied(self, message: str) -> None:
        self.lock_icon.reset_locked()
        self.status_label.setText(message)
        self.enter_button.setEnabled(True)

    def _finish_intro_animation(self) -> None:
        self._intro_animation = None
        self.panel.move(self._final_panel_pos())

    def _finish_unlock(self) -> None:
        self.lock_icon.set_unlocked()
        self.status_label.setText("Unlocked.")
        self._unlock_animation = None
        QTimer.singleShot(ANIMATION["welcome_enter_delay_ms"], self._request_enter)

    def _request_enter(self) -> None:
        self.enter_requested.emit()

    def _place_panel_at_start(self) -> None:
        self.panel.move(self._start_panel_pos())

    def _start_panel_pos(self) -> QPoint:
        final = self._final_panel_pos()
        return QPoint(final.x(), -self.panel.height() - 24)

    def _final_panel_pos(self) -> QPoint:
        return QPoint(
            max(24, (self.width() - self.panel.width()) // 2),
            max(36, (self.height() - self.panel.height()) // 2),
        )
