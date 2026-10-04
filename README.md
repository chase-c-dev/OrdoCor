# OrdoCor Life Management Application

**OrdoCor** is a private, offline-first Windows life organizer. The name combines **Ordo**
(order, rows, series, and structure) with **Cor** (core or heart).

**Release:** 1.0

## What It Manages

- Home TODOs, a year calendar, and the next seven days
- Financial accounts, investments, watchlists, CDs, collectibles, and investment plans
- Recipes with categories and images
- Projects, product wishlists, and travel ideas
- House bills, maintenance, and improvements
- Vehicles, maintenance links, and vehicle wishlists

## Private and Offline-First

OrdoCor is a local React desktop application. Personal information is stored in a SQLite database
on the computer, separate from the executable. There is no account, cloud sync, telemetry,
analytics, web server, or remote OrdoCor service.

It works especially well on a dedicated computer that never connects to the internet. On an
online computer, only ticker symbols are sent to Yahoo Finance when refreshing stock or mutual
fund information. Purchase details, notes, accounts, recipes, and other records remain local.
Live prices and chart refreshes are unavailable offline; the rest of OrdoCor continues to work.

See [Security and Privacy](docs/security.md) for the complete security model.

## Download

Non-developers can download `OrdoCor.exe` from the latest GitHub release and run it directly on
Windows. The database remains under the current Windows profile when the executable is replaced.

## Run From Source

Prerequisites: Node.js 22 or newer and Corepack.

```powershell
cd frontend
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

## Package the Executable

PowerShell:

```powershell
cd frontend
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm package
```

Command Prompt:

```cmd
cd frontend
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm package
```

The portable executable is created at `release\OrdoCor.exe`. End users do not need Node.js.

## Developer Checks

```powershell
cd frontend
corepack pnpm lint
corepack pnpm test
corepack pnpm build
```

Vitest enforces at least 97% line, statement, and function coverage for the covered renderer
modules. Native SQLite, password, and protected-backup behavior also has automated tests. GitHub
Actions runs lint, tests, production build, and Windows executable packaging on pushes and pull
requests.

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Database and Backups](docs/database.md)
- [Security and Privacy](docs/security.md)
- [Investing](docs/investing_module.md)
- [Life Modules](docs/life_modules.md)

## License

OrdoCor is licensed under [PolyForm Noncommercial 1.0.0](LICENSE). You may use, modify, and
redistribute it for purposes permitted by that license. Commercial use outside those permissions
requires a separate license from the copyright owner. Copies must include the license text or its
URL and preserve the `chase-c-dev` credit in [NOTICE](NOTICE).

As the owner of the original code, `chase-c-dev` may use that code commercially and grant separate
commercial licenses. Third-party dependencies and contributions owned by others remain subject
to their own licenses and permissions.

This is source-available software. PolyForm does not require modifications to be published and
is not an open-source license. GitHub may display it as "Other" despite its standardized name and
SPDX identifier, `PolyForm-Noncommercial-1.0.0`.
