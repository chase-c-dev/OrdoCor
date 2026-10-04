# Development

## Setup

Install Node.js 22 or newer, then run:

```powershell
cd frontend
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Vite provides hot reload while Electron supplies the same native IPC and SQLite services used by
the packaged application.

## Tests and Linting

```powershell
cd frontend
corepack pnpm lint
corepack pnpm test
corepack pnpm build
```

Vitest covers renderer utilities and native database, password, and backup services using temporary
SQLite databases. Tests never open the personal OrdoCor database and do not require market-data
network access. ESLint checks React hooks and JavaScript. Covered renderer modules enforce at least
97% line, statement, and function coverage.

Run `corepack pnpm run test:layout` from `frontend` to check the built stock-detail dialog in a
hidden Electron window at 1920x1080, 1366x768, 800x600, and 390x844. This check uses synthetic
stocks and chart data with a temporary profile. It verifies viewport sizing, centering, chart
resizing, and visible content overflow without opening the personal database or accessing the
network. Shared dialogs use React portals so page animations cannot constrain their size.

## Packaging

```powershell
cd frontend
corepack pnpm package
```

Electron Builder creates the portable Windows executable at `release\OrdoCor.exe`. Generated
`frontend/dist`, `release`, coverage, and dependency folders are ignored by Git.

The executable includes the official PolyForm Noncommercial 1.0.0 license and OrdoCor's required
attribution notices in its extracted `resources` directory. Distribute both root `LICENSE` and
`NOTICE` files with source copies. Preserve the official license text; project attribution is
declared separately in `NOTICE` using PolyForm's supported required-notice mechanism.
