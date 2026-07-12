from __future__ import annotations

import sqlite3
from importlib import resources
from pathlib import Path

from ordocor.config import prepare_database_path
from ordocor.services.local_security import harden_local_file


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> "Database":
        return cls(prepare_database_path())

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, factory=ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied_versions = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }

            migrations = resources.files("ordocor.data.migrations")
            for migration in sorted(migrations.iterdir(), key=lambda file: file.name):
                if migration.suffix != ".sql" or migration.name in applied_versions:
                    continue

                sql = migration.read_text(encoding="utf-8")
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (migration.name,),
                )
        harden_local_file(self.path)
