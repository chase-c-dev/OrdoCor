import shutil
from pathlib import Path


APP_NAME = "OrdoCor"
DATABASE_NAME = "ordocor.sqlite3"
LEGACY_APP_NAME = "LifeCore"
LEGACY_DATABASE_NAME = "lifecore.sqlite3"


def user_data_dir() -> Path:
    return Path.home() / "AppData" / "Local" / APP_NAME


def default_database_path() -> Path:
    return user_data_dir() / DATABASE_NAME


def legacy_database_path() -> Path:
    return Path.home() / "AppData" / "Local" / LEGACY_APP_NAME / LEGACY_DATABASE_NAME


def prepare_database_path() -> Path:
    destination = default_database_path()
    source = legacy_database_path()
    if not destination.exists() and source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return destination
