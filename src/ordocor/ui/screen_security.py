from __future__ import annotations

import ctypes
import os

from PySide6.QtWidgets import QWidget


WDA_MONITOR = 0x00000001
WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011


def is_screen_capture_resistance_supported() -> bool:
    return os.name == "nt"


def apply_screen_capture_resistance(widget: QWidget) -> bool:
    if not is_screen_capture_resistance_supported():
        return False

    return _set_window_display_affinity(widget, WDA_EXCLUDEFROMCAPTURE, fallback=WDA_MONITOR)


def clear_screen_capture_resistance(widget: QWidget) -> bool:
    if not is_screen_capture_resistance_supported():
        return False

    return _set_window_display_affinity(widget, WDA_NONE)


def _set_window_display_affinity(
    widget: QWidget, affinity: int, fallback: int | None = None
) -> bool:
    try:
        handle = int(widget.winId())
        user32 = ctypes.windll.user32
        if user32.SetWindowDisplayAffinity(handle, affinity):
            return True
        if fallback is None:
            return False
        return bool(user32.SetWindowDisplayAffinity(handle, fallback))
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return False
