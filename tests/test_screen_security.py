from __future__ import annotations

from types import SimpleNamespace

from ordocor.ui import screen_security


def test_screen_capture_resistance_unsupported(monkeypatch):
    monkeypatch.setattr(screen_security.os, "name", "posix")

    assert screen_security.is_screen_capture_resistance_supported() is False
    assert (
        screen_security.apply_screen_capture_resistance(SimpleNamespace(winId=lambda: 1)) is False
    )
    assert (
        screen_security.clear_screen_capture_resistance(SimpleNamespace(winId=lambda: 1)) is False
    )


def test_screen_capture_resistance_success_and_fallback(monkeypatch):
    monkeypatch.setattr(screen_security.os, "name", "nt")
    calls = []

    class FakeUser32:
        def SetWindowDisplayAffinity(self, handle, affinity):
            calls.append((handle, affinity))
            return affinity == screen_security.WDA_MONITOR

    monkeypatch.setattr(screen_security.ctypes, "windll", SimpleNamespace(user32=FakeUser32()))

    assert screen_security.is_screen_capture_resistance_supported() is True
    assert (
        screen_security.apply_screen_capture_resistance(SimpleNamespace(winId=lambda: 42)) is True
    )
    assert calls == [
        (42, screen_security.WDA_EXCLUDEFROMCAPTURE),
        (42, screen_security.WDA_MONITOR),
    ]


def test_screen_capture_resistance_primary_success_and_exception(monkeypatch):
    monkeypatch.setattr(screen_security.os, "name", "nt")

    class PrimaryUser32:
        def SetWindowDisplayAffinity(self, handle, affinity):
            return affinity == screen_security.WDA_EXCLUDEFROMCAPTURE

    monkeypatch.setattr(screen_security.ctypes, "windll", SimpleNamespace(user32=PrimaryUser32()))
    assert screen_security.apply_screen_capture_resistance(SimpleNamespace(winId=lambda: 7)) is True
    assert (
        screen_security.clear_screen_capture_resistance(SimpleNamespace(winId=lambda: 7)) is False
    )

    class BrokenWidget:
        def winId(self):
            raise RuntimeError("unavailable")

    assert screen_security.apply_screen_capture_resistance(BrokenWidget()) is False
