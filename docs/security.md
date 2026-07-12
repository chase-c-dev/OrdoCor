# Security and Privacy

OrdoCor is designed as an offline-first personal life management app. The default assumption is
that personal data should stay on the user's computer unless the user intentionally creates or
shares a backup.

## Offline-First Benefits

Most OrdoCor data is created, stored, viewed, and edited locally:

- Home TODOs, calendar items, and upcoming items
- Accounts, purchase records, plans, collectibles, CDs, and notes
- Recipes and recipe images
- Projects, wishlist items, and travel plans
- House reminders, maintenance, and improvements
- Vehicle records, maintenance, and wishlist items
- Settings, selected theme, optional password metadata, and backup timestamps

Because this information is stored locally, OrdoCor does not need a cloud account, remote login,
server sync, telemetry, analytics, or cloud backup service. This reduces exposure to remote account
takeover, cloud database breaches, server-side logging, and third-party data retention.

## Online Market Data

The Investing section can refresh live market information for stocks and mutual funds. That live
stock and mutual fund data is not available offline. When online refresh runs, OrdoCor sends the
saved ticker or mutual fund symbol to Yahoo Finance through `yfinance`.

OrdoCor does not send purchase prices, share counts, target prices, gains, notes, account names, or
other personal records with those market-data requests. The last successful market refresh and
cached chart history may remain visible while offline, but new live prices, live returns, dividend
yield updates, and refreshed charts require internet access.

## Local Database Protections

OrdoCor stores app data in a SQLite database under the user's local app data directory:

```text
C:\Users\<User>\AppData\Local\OrdoCor\ordocor.sqlite3
```

On Windows, OrdoCor attempts to harden the database file by applying current-user file permissions
and Windows file encryption after database initialization.

## Protected Backups

Backups are created from Settings and are single protected files, usually named:

```text
ordocor_backup.ordocorbackup
```

OrdoCor uses SQLite's backup API to create a consistent backup while the database is open. The
backup payload is then protected with the current Windows user's local data-protection keys. This
keeps backup creation low-friction while making copied backup files harder to read outside the
intended Windows user profile.

Settings shows the last successful backup date and time. Restore validates that a selected backup
is readable, passes SQLite integrity checks, and contains the required OrdoCor tables before
replacing the current database.

## Optional App Password

On first entry, OrdoCor offers the user the choice to create an app password or skip password setup.
Settings can later enable, change, or disable the password.

Passwords are never stored in plaintext. OrdoCor stores only a random salt, PBKDF2 iteration count,
and derived password hash in `app_settings`.

This password is an app-entry gate. It helps prevent casual access to an already installed OrdoCor
app, but it does not replace full database encryption.

## Screen Capture Resistance

On Windows, OrdoCor asks the operating system to exclude supported OrdoCor windows from common
screen capture paths. This can help reduce accidental exposure during screenshots or screen
sharing.

This setting is enabled by default. It can be turned off from Settings when the user intentionally
wants to share or record the OrdoCor window, and the preference is saved for future launches.

This is best-effort protection. It cannot stop someone from photographing the screen, and it is not
a defense against malware with sufficient access to the same Windows session.

## Sanitized Error Output

User-facing backup, restore, and market-data failures avoid showing raw operating-system exception
details, local file paths, provider internals, or other potentially sensitive text. This helps keep
private local information out of dialog messages, screenshots, and support conversations.

## Security Limits

No local desktop app can fully protect data from malware already running as the same unlocked
Windows user. While OrdoCor and Windows can read the data, sufficiently privileged malware may be
able to read it too.

The current protections are intended to reduce risk from copied files, exposed backups, other local
Windows users, accidental screenshots, casual access, and unnecessary network exposure. Stronger
protection against same-user malware or offline database extraction would require a full encrypted
database layer, such as a SQLCipher-style database key.
