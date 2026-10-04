# Security and Privacy

OrdoCor is offline-first: personal information stays on the user's computer unless the user
intentionally copies or shares a backup.

## Offline Benefits

TODOs, calendar items, accounts, purchase records, recipes, projects, wishlists, travel plans,
house information, vehicle information, settings, and images are stored locally. OrdoCor has no
cloud account, sync service, telemetry, analytics, hosted web interface, or local HTTP server. This
reduces exposure to account takeover, cloud breaches, remote logging, and third-party retention.

A dedicated computer that never connects to the internet provides the smallest network exposure.
OrdoCor also remains useful and protected on an online Windows computer.

## Online Market Data

Live stock and mutual-fund information is not available offline. When a refresh runs, OrdoCor sends
the saved ticker or fund symbol to Yahoo Finance. It does not send purchase prices, share counts,
targets, gains, notes, account names, recipes, or other life records. Cached chart history and the
last successful values remain available when offline.

## Desktop Protections

- Electron loads bundled React files directly; no network-facing OrdoCor server exists.
- The renderer is sandboxed with Node integration disabled and context isolation enabled.
- A narrow preload bridge exposes allowlisted operations to React.
- SQL resource names are allowlisted and record values are parameterized.
- External links open through the operating system instead of navigating the app window.
- Single-instance locking avoids two processes writing the same database concurrently.
- User-facing failures suppress raw paths and internal provider or operating-system details.

## Screen Capture

Native Electron content protection is enabled by default. On supported Windows versions it asks
the operating system to exclude the OrdoCor window from screenshots and screen sharing. The user
can disable **Screen Capture Resistance** in Settings when intentionally sharing OrdoCor. The saved
choice becomes the next-launch default.

## Passwords and Backups

The optional app password is hashed with PBKDF2-SHA256, a random salt, and 310,000 iterations. It
is an entry gate and is never stored in plaintext. Protected backups use an AES-256-GCM data key
wrapped by Electron `safeStorage` for the current operating-system account. Restore checks database
integrity and the expected schema before replacing local data. Settings displays the last successful
backup time.

## Security Limits

No local application can fully protect information from malware already running with the same or
higher privileges as the unlocked Windows user. The live SQLite database is not fully encrypted at
rest, and screen-capture exclusion is an operating-system request rather than an absolute guarantee.
Use a supported Windows version, a secured account, current malware protection, disk encryption,
and reliable backups for defense in depth.
