from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from ordocor.data.database import ClosingConnection, Database
from ordocor.services.local_security import (
    LocalProtectionError,
    harden_local_file,
    protect_backup_payload,
    unprotect_backup_payload,
)


LAST_BACKUP_CREATED_AT_KEY = "last_backup_created_at"


class BackupValidationError(Exception):
    """Raised when a selected backup is not a compatible OrdoCor database."""


REQUIRED_TABLES = {
    "schema_migrations",
    "app_settings",
    "investment_accounts",
    "investment_stocks",
    "investment_mutual_funds",
    "investment_banking_products",
    "investment_collectibles",
    "investment_pipeline",
    "todo_items",
    "calendar_items",
    "recipes",
    "recipe_categories",
    "projects",
    "wishlist_items",
    "travel_destinations",
    "vehicles",
    "vehicle_maintenance",
    "vehicle_wishlist",
    "house_reminders",
    "house_maintenance",
    "house_improvements",
}


class BackupService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_backup(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            suffix=".sqlite3", dir=destination.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)

        try:
            with self.database.connect() as source:
                with sqlite3.connect(temporary_path, factory=ClosingConnection) as backup:
                    source.backup(backup)

            try:
                destination.write_bytes(protect_backup_payload(temporary_path.read_bytes()))
            except LocalProtectionError as error:
                raise OSError(str(error)) from error
            harden_local_file(destination)
            self._set_last_backup_created_at(
                datetime.now().astimezone().isoformat(timespec="seconds")
            )
        finally:
            temporary_path.unlink(missing_ok=True)

        return destination

    def restore_backup(self, source_path: Path) -> Path:
        self.validate_backup(source_path)

        materialized_path = self._materialize_backup(source_path)
        try:
            with sqlite3.connect(materialized_path, factory=ClosingConnection) as source:
                with self.database.connect() as destination:
                    source.backup(destination)
        finally:
            if materialized_path != source_path:
                materialized_path.unlink(missing_ok=True)

        self.database.initialize()
        harden_local_file(self.database.path)
        return self.database.path

    def validate_backup(self, source_path: Path) -> None:
        if not source_path.exists():
            raise BackupValidationError("The selected backup file does not exist.")

        materialized_path = self._materialize_backup(source_path)
        try:
            with sqlite3.connect(materialized_path, factory=ClosingConnection) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise BackupValidationError(
                        "The selected database file failed SQLite integrity checks."
                    )

                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
        except (LocalProtectionError, sqlite3.DatabaseError) as error:
            raise BackupValidationError(
                "The selected file is not a readable SQLite database."
            ) from error
        finally:
            if materialized_path != source_path:
                materialized_path.unlink(missing_ok=True)

        missing_tables = sorted(REQUIRED_TABLES - tables)
        if missing_tables:
            missing = ", ".join(missing_tables[:5])
            if len(missing_tables) > 5:
                missing += ", ..."
            raise BackupValidationError(
                f"The selected database is missing required OrdoCor tables: {missing}."
            )

    def _materialize_backup(self, source_path: Path) -> Path:
        payload = source_path.read_bytes()
        sqlite_payload = unprotect_backup_payload(payload)
        if sqlite_payload == payload:
            return source_path

        with tempfile.NamedTemporaryFile(
            suffix=".sqlite3", dir=source_path.parent, delete=False
        ) as temporary:
            temporary.write(sqlite_payload)
            return Path(temporary.name)

    def last_backup_created_at(self) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (LAST_BACKUP_CREATED_AT_KEY,),
            ).fetchone()
        return None if row is None else row["value"]

    def _set_last_backup_created_at(self, timestamp: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (LAST_BACKUP_CREATED_AT_KEY, timestamp),
            )
