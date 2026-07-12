from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QListWidget, QTabWidget, QWidget

from ordocor import __version__
from ordocor.ui.animated_widgets import AnimatedStackedWidget, AnimatedTabWidget
from ordocor.ui.branding import APP_DISPLAY_NAME, APP_RELEASE_LABEL, app_icon
from ordocor.ui.main_window import MainWindow
from ordocor.ui.welcome import LockIcon, WelcomePage


def test_main_window_builds_every_page(qapp, database, theme_manager):
    window = MainWindow(database, theme_manager)
    window.show()
    qapp.processEvents()

    assert window.shell_stack.currentIndex() == 0
    assert window.windowTitle() == APP_DISPLAY_NAME
    assert not window.windowIcon().isNull()
    assert not app_icon().isNull()
    assert APP_RELEASE_LABEL == f"Version {'.'.join(__version__.split('.')[:2])}"
    window._enter_application()
    assert window.shell_stack.currentIndex() == 1

    navigation = window.findChild(QListWidget)
    assert [navigation.item(index).text() for index in range(navigation.count())] == [
        "Home",
        "Investing",
        "Recipes",
        "Projects",
        "Wishlist",
        "Travel",
        "House",
        "Vehicle",
    ]
    assert window.pages.count() == 8
    labels = [label.text() for label in window.findChildren(QLabel)]
    assert APP_RELEASE_LABEL in " ".join(labels)

    investing_tabs = window.pages.widget(1).findChild(QTabWidget)
    assert [investing_tabs.tabText(index) for index in range(investing_tabs.count())] == [
        "Accounts",
        "Stocks",
        "Mutual Funds",
        "Banking",
        "Collectibles",
        "Investment Plans",
    ]

    for index in range(window.pages.count()):
        navigation.setCurrentRow(index)
        assert window.pages.currentIndex() == index

    window.close()


def test_animated_navigation_widgets(qapp):
    first = QWidget()
    second = QWidget()
    stack = AnimatedStackedWidget(duration_ms=50)
    stack.addWidget(first)
    stack.addWidget(second)

    stack._fade_in_widget(None)
    stack.setCurrentIndex(-1)
    stack.setCurrentIndex(0)
    assert stack.currentIndex() == 0

    stack.setCurrentIndex(1)
    assert stack.currentIndex() == 1
    if qapp.platformName().lower() == "offscreen":
        assert stack._active_fade_animation is None
        assert second.graphicsEffect() is None
    else:
        assert stack._active_fade_animation is not None
        assert second.graphicsEffect() is not None
        stack._active_fade_animation.finished.emit()
    assert second.graphicsEffect() is None

    tab = AnimatedTabWidget()
    tab.addTab(QWidget(), "First")
    tab.addTab(QWidget(), "Second")
    tab.setCurrentIndex(1)
    assert tab.currentIndex() == 1
    if qapp.platformName().lower() == "offscreen":
        assert tab._active_fade_animation is None
    else:
        assert tab._active_fade_animation is not None


def test_welcome_page_slide_and_unlock(qapp):
    page = WelcomePage()
    page.resize(900, 640)
    start_pos = page._start_panel_pos()
    final_pos = page._final_panel_pos()
    assert start_pos.y() < 0
    assert final_pos.y() > 0

    page.show()
    qapp.processEvents()
    assert page._intro_started is True

    page.start_intro_animation()
    assert page._intro_animation is not None
    page._finish_intro_animation()
    assert page.panel.pos() == final_pos

    entered = []
    page.enter_requested.connect(lambda: entered.append(True))
    page.unlock()
    page.unlock()
    assert page._unlock_animation is not None
    assert not page.enter_button.isEnabled()
    page._finish_unlock()
    assert page.lock_icon.unlock_progress() == 1.0
    assert page.status_label.text() == "Unlocked."
    assert entered == []
    page._request_enter()
    assert entered == [True]
    page.close()


def test_lock_icon_tracks_unlock_progress(qapp):
    icon = LockIcon()
    icon.set_unlock_progress(-1)
    assert icon.unlock_progress() == 0.0
    icon.set_unlock_progress(0.5)
    assert icon.unlock_progress() == 0.5
    icon.set_unlock_progress(2)
    assert icon.unlock_progress() == 1.0
    icon.reset_locked()
    assert icon.unlock_progress() == 0.0
    icon.set_unlocked()
    assert icon.unlock_progress() == 1.0

    pixmap = QPixmap(icon.size())
    icon.render(pixmap)
    assert not pixmap.isNull()
