from __future__ import annotations

from types import SimpleNamespace

import pytest

from ordocor.services import local_security
from ordocor.services.local_security import (
    LocalProtectionError,
    PROTECTED_BACKUP_HEADER,
    protect_backup_payload,
    unprotect_backup_payload,
)


def test_protected_backup_payload_round_trips():
    payload = b"SQLite format 3\x00example"

    protected = protect_backup_payload(payload)

    assert protected.startswith(PROTECTED_BACKUP_HEADER)
    assert protected != payload
    assert unprotect_backup_payload(protected) == payload
    assert unprotect_backup_payload(payload) == payload


def test_local_security_error_paths(monkeypatch):
    class FailedCrypt32:
        def CryptProtectData(self, *args):
            return 0

        def CryptUnprotectData(self, *args):
            return 0

    fake_windows = SimpleNamespace(
        crypt32=FailedCrypt32(),
        kernel32=SimpleNamespace(LocalFree=lambda pointer: None),
    )
    monkeypatch.setattr(local_security.ctypes, "windll", fake_windows)

    with pytest.raises(LocalProtectionError, match="protect"):
        local_security.protect_bytes(b"data")

    with pytest.raises(LocalProtectionError, match="unlock"):
        local_security.unprotect_bytes(b"data")


def test_local_security_helpers(monkeypatch, tmp_path):
    assert local_security._bytes_from_blob(local_security._DataBlob()) == b""

    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(local_security, "_current_user_name", lambda: "DOMAIN\\User")
        patch.setattr(
            local_security.subprocess,
            "run",
            lambda command, **kwargs: commands.append((command, kwargs)),
        )

        protected_file = tmp_path / "ordocor.sqlite3"
        protected_file.write_text("data", encoding="utf-8")
        local_security.harden_local_file(protected_file)

    assert commands[0][0][:2] == ["icacls", str(protected_file)]
    assert commands[1][0][:2] == ["cipher", "/E"]

    monkeypatch.setattr(
        local_security.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("no command")),
    )
    local_security._run_security_command(["missing"])

    monkeypatch.delenv("USERDOMAIN", raising=False)
    monkeypatch.setenv("USERNAME", "SoloUser")
    assert local_security._current_user_name() == "SoloUser"
