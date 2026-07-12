# OrdoCor Life Management Application

**OrdoCor** is a private, offline-first desktop app for organizing everyday life in one place.

**Release Version:** 1.0

## What OrdoCor Helps Manage

- **Home:** TODOs, yearly calendar, and upcoming items
- **Investing:** accounts, stocks, mutual funds, CDs, collectibles, and investment plans
- **Recipes:** favorite recipes in a cookbook-style view
- **Projects:** active personal projects
- **Wishlist:** products you want to buy
- **Travel:** countries and cities you want to visit
- **House:** tax and insurance reminders, maintenance, and improvements
- **Vehicle:** vehicles, maintenance, and wishlist items

## Privacy and Security

OrdoCor is built to keep personal information local.

- Your data is stored on your computer in a local SQLite database.
- There is no cloud account, server sync, telemetry, analytics, or cloud backup.
- For the strongest security, OrdoCor works very well on a dedicated offline computer that is
  never connected to the internet.
- On an online computer, OrdoCor still keeps personal records local while offering online features
  like live stock and mutual fund market data.
- Backups are created manually from Settings.
- On Windows, OrdoCor applies local file protections and creates protected backup files.
- You can optionally enable an OrdoCor password.
- OrdoCor attempts to reduce screen-capture exposure on supported Windows systems.
- Error messages avoid showing sensitive file paths or raw system details.

The only online feature is live market data for stocks and mutual funds. When that refreshes,
OrdoCor sends the ticker or fund symbol to Yahoo Finance through `yfinance`. Purchase prices,
share counts, gains, notes, account names, and other personal records stay local.

Live stock and mutual fund prices are not available offline. Cached values may remain visible, but
fresh market prices and chart updates require internet access.

## Run the App

Non-developers should use the latest executable from GitHub Releases:

[Download the latest OrdoCor release](https://github.com/chase-c-dev/Lifecore/releases/latest)

Developers can run OrdoCor from source:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m ordocor
```

## Package the Executable

PowerShell:

```powershell
python -m PyInstaller `
  --name OrdoCor `
  --windowed `
  --onefile `
  --icon src\ordocor\assets\ordocor_icon.ico `
  --collect-data ordocor `
  src\ordocor\main.py
```

Command Prompt:

```cmd
python -m PyInstaller ^
  --name OrdoCor ^
  --windowed ^
  --onefile ^
  --icon src\ordocor\assets\ordocor_icon.ico ^
  --collect-data ordocor ^
  src\ordocor\main.py
```

The executable is created at:

```text
dist\OrdoCor.exe
```

## Documentation

- [Security and Privacy](docs/security.md)
- [Database and Backups](docs/database.md)
- [Life Modules](docs/life_modules.md)
- [Investing Module](docs/investing_module.md)
- [Development](docs/development.md)
- [Architecture](docs/architecture.md)

## License

OrdoCor is released under a non-commercial public modification license. You may view, use, copy,
and modify the code for non-commercial purposes.

Requirements:

- Credit `chase-c-dev` for the original code.
- Do not sell the app, include it in a paid product, or use it commercially without permission.
- Any modifications, forks, or derivative versions must make their complete source code public.
- Modified versions must keep the same license terms.

See [LICENSE](LICENSE) for the full license.

## Developer Checks

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Tests use isolated temporary databases and do not modify personal OrdoCor data.
