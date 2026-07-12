# Architecture

## Product Direction

OrdoCor is a personal life management desktop application. It is built to work offline, store data locally, and eventually package as a Windows executable.

Current app sections:

- Home
- Investing
- Recipes
- Projects
- Wishlist
- Travel
- House
- Vehicle
- Settings

Each major section is implemented as a separate page under `src/ordocor/ui/pages/` and shares the same SQLite database layer.

## Desktop GUI

OrdoCor uses **PySide6**, the Qt for Python binding.

Reasons:

- Modern native desktop widgets
- Stable and actively maintained
- Free under LGPL
- Good support for dark themed desktop apps
- Works with PyInstaller for executable packaging

Main UI structure:

```text
src/ordocor/ui/
  animated_widgets.py     Reusable fade-enabled stacked and tab widgets
  main_window.py          App shell, navigation, Settings dialog
  welcome.py              Animated startup welcome and unlock screen
  screen_security.py      Windows display-affinity helper for capture resistance
  design_config.py        Global design tokens for fonts, spacing, radii, and controls
  theme/                  App-wide Qt stylesheet, palettes, and theme manager
  pages/
    home/                  TODO, calendar, upcoming, and dialogs
    investing/             One module per investing tab
    recipes/               Page, editor dialog, and repository
    projects/              Page and editor dialog
    wishlist/              Page and editor dialog
    travel/                Page and editor dialog
    house/                 Tax/insurance reminders, maintenance, and improvements
    vehicle/               Vehicles, maintenance, and wishlist items
    property_dialogs.py    Shared form dialog helpers for house and vehicle pages
```

Global design values that should be easy to tune live in `src/ordocor/ui/design_config.py`.
This file contains the shared font, button, tab, input, table, list, scrollbar, and calendar
button settings used by the stylesheet and special-purpose controls. Color palette values remain
in `src/ordocor/ui/theme/palettes.py`, while stylesheet generation and theme application live
under `src/ordocor/ui/theme/`.

The main window starts on a welcome entry screen and transitions into the application shell after
the user selects **Enter OrdoCor**. Main page navigation and Investing subtabs use the reusable
fade widgets in `src/ordocor/ui/animated_widgets.py`.

## Data Layer

OrdoCor uses **SQLite** through Python's standard `sqlite3` module.

Default database path:

```text
C:\Users\<User>\AppData\Local\OrdoCor\ordocor.sqlite3
```

On first launch after the rename, OrdoCor copies an existing legacy
`LifeCore\lifecore.sqlite3` database to the new location when an OrdoCor database does not already
exist. The original legacy file is left untouched as a precaution.

Database code:

```text
src/ordocor/data/database.py
src/ordocor/data/migrations/
```

Schema changes are stored as numbered SQL migration files. Applied migrations are tracked in the `schema_migrations` table.

## Services

The backup and restore logic lives in:

```text
src/ordocor/services/backup_service.py
src/ordocor/services/local_security.py
src/ordocor/services/password_service.py
```

Backups use SQLite's backup API and are then wrapped in Windows user-bound local data protection
for a no-password protected backup file. Restore validates that the selected backup is readable,
passes integrity checks, and contains required OrdoCor tables before replacing the active database.
The local security helper also attempts current-user file permission hardening and Windows file
encryption for database and backup files where the operating system supports it.

The optional app password uses `PasswordService`, which stores only salted PBKDF2 password hashes
and related metadata in `app_settings`. The welcome screen offers setup the first time the user
enters the app, and Settings exposes enable, change, and disable controls.

The main window and Settings dialog call `src/ordocor/ui/screen_security.py` on show to request
Windows screen-capture resistance through display affinity. Backup and restore UI messages are
sanitized so raw OS exception strings are not shown to users.

## Offline Behavior

OrdoCor is offline-first:

- Local data entry and viewing work without internet.
- No telemetry, analytics, account sync, or cloud backup calls are implemented.
- User data remains in the local SQLite database unless the user manually exports a backup.
- Protected backups use Windows local data protection without adding an OrdoCor password prompt.
- Users can optionally enable an OrdoCor password gate from first entry or Settings.
- Supported Windows windows request screen-capture resistance while OrdoCor is open.
- Stock ticker and mutual fund symbols are sent to Yahoo Finance through `yfinance` when the user
  enters the corresponding tab or opens a security chart. Cached quotes and chart history remain
  available offline.
- Future online features should be optional and should not block app startup.

## Packaging

Executable packaging uses PyInstaller:

```powershell
python -m PyInstaller `
  --name OrdoCor `
  --windowed `
  --onefile `
  --icon src\ordocor\assets\ordocor_icon.ico `
  --collect-data ordocor `
  src\ordocor\main.py
```

The build output is `dist\OrdoCor.exe`. The packaging command collects OrdoCor data files so
migration SQL files and app assets are available inside the executable.

## Automated Quality

OrdoCor uses three complementary quality checks:

- **Pytest** exercises the database, services, application entry points, dialogs, page behavior,
  CRUD workflows, settings, themes, and main-window structure.
- **pytest-cov** measures the `ordocor` package and requires 100% statement coverage.
- **Ruff** provides Python linting and formatting checks.

The tests live in `tests/`. Shared fixtures in `tests/conftest.py` create an offscreen Qt
application and isolated SQLite databases, preventing tests from reading or changing the user's
real OrdoCor database. The main test modules are organized by application area:

```text
tests/
  conftest.py                       Shared Qt, database, and theme fixtures
  test_database.py                 Schema, validation, and theme persistence
  test_dialogs.py                  Dialog input and output behavior
  test_entrypoints.py              Startup and configuration paths
  test_home.py                     TODO, calendar, and upcoming workflows
  test_investing.py                Investing pages and CRUD behavior
  test_life_pages.py               Projects, wishlist, and travel
  test_local_security.py           Windows-bound backup and file protection helpers
  test_password_security.py        Optional password service, dialogs, and entry flow
  test_property_pages.py           House and vehicle workflows
  test_recipes.py                  Recipe repository and page behavior
  test_screen_security.py          Screen-capture resistance helper behavior
  test_services_and_settings.py    Backup, restore, and settings
  test_ui_structure.py             Main-window page composition
```

Qt uses the `offscreen` platform during automated runs, so tests do not open visible windows.
Temporary files are placed under `test_outputs/`. The Pytest
`tmp_path_retention_policy = "failed"` setting retains temporary output only for failed tests;
successful test output is deleted to reduce workspace clutter. The directory is excluded from
version control.

The GitHub Actions workflow in `.github/workflows/quality.yml` installs OrdoCor as an editable
package, verifies that `ordocor.data` is importable, and then runs linting, formatting, and tests
on Windows with Python 3.11. It runs for every push and pull request and uploads `coverage.xml`
when available.

Local commands and setup instructions are maintained in `docs/development.md`.
