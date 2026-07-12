from __future__ import annotations

import runpy
from pathlib import Path

import pytest

import ordocor.main as main_module
from ordocor import app as app_module
from ordocor import config, main
from ordocor.data.database import Database


def test_config_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config.user_data_dir() == tmp_path / "AppData" / "Local" / "OrdoCor"
    assert config.default_database_path().name == "ordocor.sqlite3"
    assert Database.default().path == config.default_database_path()


def test_existing_lifecore_database_is_copied_to_ordocor(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    legacy_path = config.legacy_database_path()
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_bytes(b"existing database")

    destination = Database.default().path

    assert destination == config.default_database_path()
    assert destination.read_bytes() == b"existing database"
    assert legacy_path.exists()


def test_database_reinitialize_skips_applied_migrations(database):
    database.initialize()
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] > 0


def test_main_delegates(monkeypatch):
    monkeypatch.setattr(main, "run_app", lambda: 7)
    assert main.main() == 7


def test_run_app_wires_components(monkeypatch, tmp_path):
    calls = []

    class FakeApplication:
        def __init__(self, argv):
            calls.append(("app", argv))

        def setApplicationName(self, name):
            calls.append(("name", name))

        def setOrganizationName(self, name):
            calls.append(("organization", name))

        def setWindowIcon(self, icon):
            calls.append(("icon", icon.isNull()))

        def exec(self):
            return 3

    class FakeDatabase:
        @classmethod
        def default(cls):
            return cls()

        def initialize(self):
            calls.append(("initialize",))

    class FakeWindow:
        def __init__(self, **kwargs):
            calls.append(("window", kwargs))

        def resize(self, width, height):
            calls.append(("resize", width, height))

        def show(self):
            calls.append(("show",))

    monkeypatch.setattr(app_module, "QApplication", FakeApplication)
    monkeypatch.setattr(app_module, "Database", FakeDatabase)
    monkeypatch.setattr(app_module, "ThemeManager", lambda database, app: "theme")
    monkeypatch.setattr(app_module, "MainWindow", FakeWindow)
    assert app_module.run_app() == 3
    assert ("name", "OrdoCor") in calls
    assert ("icon", False) in calls
    assert ("resize", 1200, 760) in calls


def test_executable_bootstrap_modules(monkeypatch):
    monkeypatch.setattr(app_module, "run_app", lambda: 5)
    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
        with pytest.raises(SystemExit, match="5"):
            runpy.run_module("ordocor.main", run_name="__main__")

    monkeypatch.setattr(main_module, "main", lambda: 6)
    with pytest.raises(SystemExit, match="6"):
        runpy.run_module("ordocor.__main__", run_name="__main__")
