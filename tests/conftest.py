from __future__ import annotations

import gc
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from ordocor.data.database import Database
from ordocor.ui.theme import ThemeManager


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def database(tmp_path) -> Database:
    database = Database(tmp_path / "ordocor.sqlite3")
    database.initialize()
    return database


@pytest.fixture
def theme_manager(qapp, database) -> ThemeManager:
    manager = ThemeManager(database, qapp)
    yield manager
    manager.close()
    manager.setParent(None)
    manager.deleteLater()
    qapp.processEvents()
    gc.collect()
