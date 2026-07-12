from __future__ import annotations

import ctypes
import os
import subprocess
from ctypes import wintypes
from pathlib import Path


PROTECTED_BACKUP_HEADER = b"ORDOCOR-DPAPI-BACKUP-v1\n"


class LocalProtectionError(Exception):
    """Raised when Windows local data protection cannot protect or unprotect data."""


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def is_windows() -> bool:
    return os.name == "nt"


def protect_bytes(data: bytes) -> bytes:
    if not is_windows():  # pragma: no cover - OrdoCor currently targets Windows.
        return data

    input_blob, input_buffer = _blob_from_bytes(data)
    output_blob = _DataBlob()
    try:
        if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            "OrdoCor local backup".encode("utf-16-le"),
            None,
            None,
            None,
            0,
            ctypes.byref(output_blob),
        ):
            raise LocalProtectionError("Windows could not protect the backup data.")
        return _bytes_from_blob(output_blob)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
        ctypes.memset(ctypes.addressof(input_buffer), 0, len(input_buffer))


def unprotect_bytes(data: bytes) -> bytes:
    if not is_windows():  # pragma: no cover - OrdoCor currently targets Windows.
        return data

    input_blob, input_buffer = _blob_from_bytes(data)
    output_blob = _DataBlob()
    try:
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(output_blob),
        ):
            raise LocalProtectionError(
                "Windows could not unlock this protected backup. It may belong to a "
                "different Windows user or computer."
            )
        return _bytes_from_blob(output_blob)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
        ctypes.memset(ctypes.addressof(input_buffer), 0, len(input_buffer))


def protect_backup_payload(sqlite_payload: bytes) -> bytes:
    return PROTECTED_BACKUP_HEADER + protect_bytes(sqlite_payload)


def unprotect_backup_payload(payload: bytes) -> bytes:
    if not payload.startswith(PROTECTED_BACKUP_HEADER):
        return payload
    return unprotect_bytes(payload.removeprefix(PROTECTED_BACKUP_HEADER))


def harden_local_file(path: Path) -> None:
    if not is_windows() or not path.exists():  # pragma: no cover - platform guard.
        return

    _run_security_command(["icacls", str(path), "/grant:r", f"{_current_user_name()}:F"])
    _run_security_command(["cipher", "/E", str(path)])


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer


def _bytes_from_blob(blob: _DataBlob) -> bytes:
    if not blob.pbData:
        return b""
    return ctypes.string_at(blob.pbData, blob.cbData)


def _run_security_command(command: list[str]) -> None:
    try:
        subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError:
        return


def _current_user_name() -> str:
    domain = os.environ.get("USERDOMAIN")
    username = os.environ.get("USERNAME") or os.environ.get("USER") or os.getlogin()
    if domain and username:
        return f"{domain}\\{username}"
    return username
