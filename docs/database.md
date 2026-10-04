# Database and Backups

## Database

All OrdoCor records are stored in one local SQLite database:

```text
C:\Users\<User>\AppData\Local\OrdoCor\ordocor.sqlite3
```

The database is separate from `OrdoCor.exe`, so replacing the executable does not remove user
data. Electron creates missing tables from `frontend/electron/schema.sql` and continues to use an
existing compatible database at that location.

The database includes life records, recipe images, market-history cache, optional password
metadata, theme preferences, privacy-screen preference, and the last successful backup time.
Passwords are represented only by a random salt, PBKDF2 iteration count, and derived hash.

## Backup and Restore

**Settings > Create Backup** writes one `.ordocorbackup` file. SQLite's backup API first creates a
consistent snapshot. The snapshot is encrypted with AES-256-GCM, and its random encryption key is
wrapped by Electron `safeStorage`, which uses the current operating-system account protection.
No extra backup password is required.

**Settings > Load Backup** accepts current protected backups and compatible plain SQLite backups.
Before replacement, OrdoCor verifies SQLite integrity and checks for every required table. An
invalid file leaves the current database unchanged. User-facing errors omit raw local paths and
internal exception details.

Protected backups are intended for the same Windows account. Protected `.ordocorbackup` files from
the retired Python release used a different wrapper and should be restored with that release before
upgrading; the normal on-disk database itself remains compatible.

## Limits

The optional password controls entry to the application, and protected backup files are encrypted.
The live SQLite database is not fully encrypted at rest. Windows account security, drive encryption
such as BitLocker, current patches, and malware protection remain important.
