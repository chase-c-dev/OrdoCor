# Database and Backups

## Database

OrdoCor stores all app data in a local SQLite database.

Default path:

```text
C:\Users\<User>\AppData\Local\OrdoCor\ordocor.sqlite3
```

When OrdoCor starts and no database exists at this path, it checks the previous
`LifeCore\lifecore.sqlite3` location. If found, the database is copied into the OrdoCor directory;
the original file remains in place.

The database file is separate from the executable. This makes the app offline-first and keeps user
data local. On Windows, OrdoCor attempts to harden the database file with current-user file
permissions and Windows file encryption after schema initialization.

## Migrations

Schema migrations live in:

```text
src/ordocor/data/migrations/
```

The app creates a `schema_migrations` table and records each applied migration filename.

Five-year stock and mutual-fund chart history is cached in `market_price_history`. Security notes
remain in the existing `notes` fields on `investment_stocks` and `investment_mutual_funds`.
House and Vehicle data is stored in dedicated tables for reminders, maintenance, improvements,
vehicles, and vehicle wishlist items so the information is included in the same database backup.
Optional app password settings are also stored in `app_settings`. Passwords are never stored in
plaintext; OrdoCor stores a random salt, PBKDF2 iteration count, and derived password hash.
The last successful backup timestamp is stored in `app_settings` and displayed in Settings.

## Optional Password

On first entry, OrdoCor offers the user the choice to create an app password or skip password
setup. If enabled, the welcome screen asks for the password before opening the main workspace.
Settings can enable, change, or disable this password later.

The password is an application access gate and convenience security layer. It does not replace
full database encryption. The database still relies on Windows local file protections and protected
backup wrapping unless a future SQLCipher-style encrypted database layer is added.

## Backup

Backups are created from **Settings > Create Backup**.

The backup is a single protected file, usually named:

```text
ordocor_backup.ordocorbackup
```

SQLite's backup API is used instead of direct file copying, so backups can be created while the
database is open. The SQLite backup payload is then protected with the current Windows user's local
data-protection keys. This avoids a separate password prompt, but it also means protected backups
are intended for the same Windows user profile. Older plain SQLite backups are still accepted by
restore for compatibility.

Settings shows the last successful backup date and time. Failed backup and restore messages avoid
showing raw operating-system exception details, file paths, or other potentially sensitive text.

## Restore

Backups are loaded from **Settings > Load Backup**.

Before restore, OrdoCor validates that the selected file:

- Exists
- Is a readable protected OrdoCor backup or legacy SQLite database
- Passes `PRAGMA integrity_check`
- Contains required OrdoCor tables

If validation fails, the current local database is left unchanged and an error message is shown.

## Privacy

OrdoCor has no server sync, telemetry, analytics, login, or cloud backup. Personal records stay
local unless the user manually copies or shares a database backup. Entering a market-data tab or
opening a security chart sends saved stock ticker or mutual fund symbols to Yahoo Finance through
`yfinance`; it does not send purchase prices, share counts, target prices, gains, notes, or other
personal records.

The default no-password security model is intentionally low-friction. It helps protect copied
database files, protected backups, and access from other Windows users, but malware already running
as the same unlocked Windows user may still be able to read data while OrdoCor or Windows itself
can read it. Enabling the optional OrdoCor password adds an app-entry gate. Stronger protection
against same-user malware or offline database extraction would require a full SQLCipher-style
encrypted database key.

On Windows, OrdoCor also asks the operating system to exclude supported OrdoCor windows from common
screen capture paths. This is best-effort protection against accidental screenshots or screen
sharing; it is not a defense against malware with sufficient local access or external cameras.
