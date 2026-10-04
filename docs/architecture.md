# Architecture

OrdoCor is a React desktop application packaged with Electron.

```text
React renderer
      |
      | restricted Electron IPC bridge
      v
Electron main process
      |
      +-- local SQLite database
      +-- protected backup and password services
      +-- native file dialogs and screen-capture protection
      +-- Yahoo Finance market-data provider when online
```

## Runtime

Electron opens a native OrdoCor window and loads the bundled React files directly from the
executable. It does not start an HTTP server, bind a port, or require a browser. The preload script
exposes only the small `invoke` and `openExternal` bridge used by the renderer. Node integration is
disabled, context isolation is enabled, and the renderer is sandboxed.

The application keeps its SQLite database at `%LOCALAPPDATA%\OrdoCor\ordocor.sqlite3`, preserving
the same user-data location used by prior releases.

## Desktop Layer

- `frontend/electron/main.cjs`: native window, IPC routes, dialogs, and content protection
- `frontend/electron/database.cjs`: allowlisted SQLite CRUD and cached market history
- `frontend/electron/schema.sql`: complete database schema
- `frontend/electron/backup.cjs`: consistent, protected backup creation and validation
- `frontend/electron/security.cjs`: optional password hashing and verification
- `frontend/electron/market.cjs`: optional Yahoo Finance quotes, charts, and More Info
- `frontend/electron/preload.cjs`: restricted renderer bridge

Table and column names are selected from allowlists rather than renderer input, and all record
values are parameterized.

## React Layer

- `frontend/src/App.jsx`: welcome screen, navigation, and application shell
- `frontend/src/components`: reusable modal, form, table, chart, and page primitives
- `frontend/src/pages`: Home, Investing, Recipes, House, Vehicle, and Settings views
- `frontend/src/config/resources.js`: shared field and display definitions
- `frontend/src/styles.css`: global layout, themes, interactions, and responsive behavior
