# Development

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run the App

```powershell
python -m ordocor
```

## Run Tests

From the repository root, run:

```powershell
python -m pytest
```

Pytest measures the `ordocor` package and fails if statement coverage drops below 100%. It also
creates `coverage.xml` for CI and coverage tooling. Tests use temporary SQLite databases and Qt's
offscreen platform, so they do not change the user's OrdoCor database or open GUI windows.

Temporary test files use the local `test_outputs/` directory. Successful test output is removed
automatically because `tmp_path_retention_policy` is set to `failed`; output from failed tests is
retained for debugging. `test_outputs/` is ignored by Git.

Useful Pytest commands:

```powershell
# Run one test module
python -m pytest tests/test_home.py

# Run tests whose names contain a phrase
python -m pytest -k backup

# Show more detailed test names
python -m pytest -v
```

Coverage remains enforced for these commands through `pyproject.toml`.

## Lint

```powershell
python -m ruff check .
```

## Format Check

```powershell
python -m ruff format --check .
```

To apply Ruff formatting locally, run `python -m ruff format .`.

## Run All Quality Checks

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

GitHub Actions runs this same sequence on every push and pull request using Python 3.11 on
Windows. The workflow first verifies that the installed package can import `ordocor.data`, which
provides a clearer error if package installation or tracked source files are incomplete.

## Test Configuration

Test, coverage, and Ruff settings are centralized in `pyproject.toml`. Important generated files
and directories are excluded through `.gitignore`:

- `coverage.xml` contains the machine-readable coverage report.
- `.coverage` is pytest-cov's local coverage data file.
- `test_outputs/` contains temporary output retained from failed tests.
- `.pytest_cache/` and `.ruff_cache/` contain tool caches.

## Compile Check

```powershell
python -m compileall src tests
```

## Build Executable

Executable packaging uses PyInstaller.

```powershell
python -m PyInstaller `
  --name OrdoCor `
  --windowed `
  --onefile `
  --icon src\ordocor\assets\ordocor_icon.ico `
  --collect-data ordocor `
  src\ordocor\main.py
```

The executable is created at `dist\OrdoCor.exe`. The `--collect-data ordocor` option includes
bundled migration SQL files and app assets.

## Source Layout

```text
src/ordocor/
  app.py
  config.py
  main.py
  data/
    database.py
    migrations/
  services/
    backup_service.py
  ui/
    main_window.py
    theme.py
    pages/
```

## Common Notes

- The run command is `python -m ordocor`.
- The visible app name is `OrdoCor`.
- The package/import name is lowercase: `ordocor`.
- The local database is stored under `%LOCALAPPDATA%\OrdoCor\ordocor.sqlite3`.
- The full name `OrdoCor Life Management Application` is reserved for the README and GitHub.
