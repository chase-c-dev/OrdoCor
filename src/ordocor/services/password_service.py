from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from ordocor.data.database import Database


PASSWORD_ENABLED_KEY = "password_enabled"
PASSWORD_HASH_KEY = "password_hash"
PASSWORD_ITERATIONS_KEY = "password_iterations"
PASSWORD_PROMPT_SEEN_KEY = "password_prompt_seen"
PASSWORD_SALT_KEY = "password_salt"
PBKDF2_ITERATIONS = 310_000


class PasswordService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def has_seen_setup_prompt(self) -> bool:
        return self._get_setting(PASSWORD_PROMPT_SEEN_KEY) == "1"

    def mark_setup_prompt_seen(self) -> None:
        self._set_setting(PASSWORD_PROMPT_SEEN_KEY, "1")

    def is_enabled(self) -> bool:
        return (
            self._get_setting(PASSWORD_ENABLED_KEY) == "1"
            and self._get_setting(PASSWORD_HASH_KEY) is not None
            and self._get_setting(PASSWORD_SALT_KEY) is not None
        )

    def set_password(self, password: str) -> None:
        if not password:
            raise ValueError("Password cannot be empty.")

        salt = secrets.token_bytes(16)
        password_hash = self._hash_password(password, salt, PBKDF2_ITERATIONS)
        self._set_setting(PASSWORD_SALT_KEY, base64.b64encode(salt).decode("ascii"))
        self._set_setting(PASSWORD_HASH_KEY, base64.b64encode(password_hash).decode("ascii"))
        self._set_setting(PASSWORD_ITERATIONS_KEY, str(PBKDF2_ITERATIONS))
        self._set_setting(PASSWORD_ENABLED_KEY, "1")
        self.mark_setup_prompt_seen()

    def disable_password(self) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                DELETE FROM app_settings
                WHERE key IN (?, ?, ?, ?)
                """,
                (
                    PASSWORD_ENABLED_KEY,
                    PASSWORD_HASH_KEY,
                    PASSWORD_ITERATIONS_KEY,
                    PASSWORD_SALT_KEY,
                ),
            )
        self.mark_setup_prompt_seen()

    def verify_password(self, password: str) -> bool:
        salt_value = self._get_setting(PASSWORD_SALT_KEY)
        hash_value = self._get_setting(PASSWORD_HASH_KEY)
        iterations_value = self._get_setting(PASSWORD_ITERATIONS_KEY)
        if not salt_value or not hash_value or not iterations_value:
            return False

        try:
            salt = base64.b64decode(salt_value)
            expected_hash = base64.b64decode(hash_value)
            iterations = int(iterations_value)
        except (ValueError, TypeError):
            return False

        actual_hash = self._hash_password(password, salt, iterations)
        return hmac.compare_digest(actual_hash, expected_hash)

    def _get_setting(self, key: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (key,),
            ).fetchone()
        return None if row is None else row["value"]

    def _set_setting(self, key: str, value: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def _hash_password(self, password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
