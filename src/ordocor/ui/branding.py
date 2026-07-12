from __future__ import annotations

from importlib import resources

from PySide6.QtGui import QIcon

from ordocor import __version__


APP_DISPLAY_NAME = "OrdoCor"
APP_RELEASE_LABEL = f"Version {'.'.join(__version__.split('.')[:2])}"


def app_icon() -> QIcon:
    icon_path = resources.files("ordocor").joinpath("assets", "ordocor_icon.svg")
    return QIcon(str(icon_path))
