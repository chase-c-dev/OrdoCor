const fs = require('node:fs')
const path = require('node:path')
const { app, BrowserWindow, dialog, ipcMain, safeStorage, shell } = require('electron')
const { BackupService } = require('./backup.cjs')
const { OrdoCorDatabase, AppError } = require('./database.cjs')
const market = require('./market.cjs')
const { MARKET_RESOURCES } = require('./resources.cjs')
const { PasswordService } = require('./security.cjs')

app.setName('OrdoCor')
if (process.env.LOCALAPPDATA) app.setPath('userData', path.join(process.env.LOCALAPPDATA, 'OrdoCor'))

let mainWindow; let database; let passwords; let backups; let unlocked = false
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) app.quit()

function screenCaptureEnabled() { return database.getSetting('screen_capture_resistance_enabled') !== '0' }

function recordStartupFailure(code) {
  const safeCode = String(code || 'STARTUP_ERROR').replace(/[^a-z0-9_-]/gi, '').slice(0, 48) || 'STARTUP_ERROR'
  try {
    fs.mkdirSync(app.getPath('userData'), { recursive: true })
    fs.writeFileSync(path.join(app.getPath('userData'), 'startup-error.log'), `${new Date().toISOString()} ${safeCode}\n`)
  } catch {
    // The error dialog still gives the user a recovery path if diagnostics cannot be written.
  }
  return safeCode
}

function stopAfterStartupFailure(error) {
  const code = recordStartupFailure(error?.code || error?.name)
  dialog.showErrorBox(
    'OrdoCor could not start',
    `OrdoCor encountered a local startup problem and did not open. Your database was not modified. Error code: ${code}`,
  )
  app.quit()
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1320, height: 820, minWidth: 760, minHeight: 620, show: false,
    backgroundColor: '#101218', icon: path.join(__dirname, '..', 'build', 'ordocor_icon.ico'),
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  })
  mainWindow.setContentProtection(screenCaptureEnabled())
  mainWindow.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:\/\//i.test(url)) shell.openExternal(url); return { action: 'deny' } })
  mainWindow.webContents.on('will-navigate', (event, url) => { if (url !== mainWindow.webContents.getURL()) event.preventDefault() })
  const revealTimer = setTimeout(() => { if (!mainWindow.isDestroyed() && !mainWindow.isVisible()) mainWindow.show() }, 3000)
  mainWindow.once('ready-to-show', () => { clearTimeout(revealTimer); mainWindow.show() })
  mainWindow.once('closed', () => clearTimeout(revealTimer))
  mainWindow.webContents.on('did-fail-load', () => {
    recordStartupFailure('RENDER_LOAD_FAILED')
    dialog.showErrorBox('OrdoCor interface did not load', 'The local interface could not be displayed. Your database was not modified.')
    if (!mainWindow.isDestroyed()) mainWindow.show()
  })
  mainWindow.webContents.on('render-process-gone', () => {
    recordStartupFailure('RENDER_PROCESS_STOPPED')
    dialog.showErrorBox('OrdoCor interface stopped', 'The local interface stopped unexpectedly. Your database was not modified.')
  })
  if (app.isPackaged) mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  else mainWindow.loadURL('http://127.0.0.1:5173')
}

function requireAccess(pathname) {
  const publicPaths = ['/status', '/auth/unlock', '/auth/password', '/auth/setup-skip']
  if (!publicPaths.includes(pathname) && passwords.isEnabled() && !unlocked) throw new AppError('OrdoCor is locked.', 401)
}

async function route(rawPath, options = {}) {
  const url = new URL(rawPath, 'ordocor://local'); const pathname = url.pathname; const method = options.method || 'GET'; const body = options.body || {}
  requireAccess(pathname)
  if (pathname === '/status') return { name: 'OrdoCor', version: '1.0', passwordEnabled: passwords.isEnabled(), setupSeen: passwords.hasSeenPrompt(), unlocked }
  if (pathname === '/auth/unlock' && method === 'POST') { if (!passwords.isEnabled() || passwords.verify(body.password || '')) { unlocked = true; return { unlocked: true } } throw new AppError('The password was not correct.', 401) }
  if (pathname === '/auth/password' && method === 'POST') { if (passwords.isEnabled() && !passwords.verify(body.currentPassword || '')) throw new AppError('The current password was not correct.', 401); passwords.setPassword(body.password || ''); unlocked = true; return { enabled: true } }
  if (pathname === '/auth/password' && method === 'DELETE') { if (passwords.isEnabled() && !passwords.verify(body.password || '')) throw new AppError('The password was not correct.', 401); passwords.disable(); unlocked = true; return { enabled: false } }
  if (pathname === '/auth/setup-skip' && method === 'POST') { passwords.markPromptSeen(); unlocked = true; return { unlocked: true } }
  if (pathname === '/quit' && method === 'POST') { setTimeout(() => app.quit(), 50); return { closing: true } }

  const resourceMatch = pathname.match(/^\/resources\/([^/]+)(?:\/(\d+))?$/)
  if (resourceMatch) {
    const [, name, id] = resourceMatch; const parent = url.searchParams.get('parent_id')
    if (method === 'GET' && !id) return database.list(name, parent ? Number(parent) : null)
    if (method === 'POST' && !id) return database.create(name, body)
    if (method === 'PUT' && id) return database.update(name, Number(id), body)
    if (method === 'DELETE' && id) return database.remove(name, Number(id))
  }
  if (pathname === '/home/upcoming') return database.upcoming()

  const imageMatch = pathname.match(/^\/recipes\/(\d+)\/image$/)
  if (imageMatch && method === 'GET') return database.recipeImage(Number(imageMatch[1]))
  if (imageMatch && method === 'PUT') return database.setRecipeImage(Number(imageMatch[1]), body.bytes, body.name)

  const refreshMatch = pathname.match(/^\/market\/([^/]+)\/refresh$/)
  if (refreshMatch && method === 'POST') {
    const mapping = MARKET_RESOURCES[refreshMatch[1]]; if (!mapping) throw new AppError('Unknown market resource.', 404)
    const [table, column] = mapping; const symbols = database.db.prepare(`SELECT DISTINCT ${column} AS symbol FROM ${table} WHERE TRIM(${column}) != ''`).all()
    let updated = 0; let failed = 0
    for (const row of symbols) { try { const result = await market.quote(row.symbol); database.db.prepare(`UPDATE ${table} SET market_price = ?, dividend_yield = ?, market_updated_at = ? WHERE UPPER(${column}) = ?`).run(result.market_price, result.dividend_yield, result.fetched_at, result.ticker); updated++ } catch { failed++ } }
    return { updated, failed }
  }
  const historyMatch = pathname.match(/^\/market\/([^/]+)\/history$/)
  if (historyMatch) { const symbol = decodeURIComponent(historyMatch[1]).toUpperCase(); try { const rows = await market.history(symbol); database.cacheHistory(symbol, rows); return rows } catch { const cached = database.history(symbol); if (cached.length) return cached; throw new AppError('Market history is unavailable.', 503) } }
  const infoMatch = pathname.match(/^\/market\/([^/]+)\/fundamentals$/)
  if (infoMatch) { try { return await market.fundamentals(decodeURIComponent(infoMatch[1])) } catch { throw new AppError('More information is unavailable.', 503) } }

  if (pathname === '/settings' && method === 'GET') return { theme: database.getSetting('color_palette') || 'Moonlit', lastBackup: database.getSetting('last_backup_created_at'), passwordEnabled: passwords.isEnabled(), screenCaptureEnabled: screenCaptureEnabled() }
  if (pathname === '/settings' && method === 'PUT') { if (body.theme) database.setSetting('color_palette', body.theme); if (typeof body.screenCaptureEnabled === 'boolean') { database.setSetting('screen_capture_resistance_enabled', body.screenCaptureEnabled ? '1' : '0'); mainWindow.setContentProtection(body.screenCaptureEnabled) } return { saved: true } }
  if (pathname === '/backup' && method === 'POST') { const result = await dialog.showSaveDialog(mainWindow, { title: 'Backup OrdoCor Database', defaultPath: `ordocor-backup-${new Date().toISOString().slice(0, 10)}.ordocorbackup`, filters: [{ name: 'OrdoCor Backup', extensions: ['ordocorbackup'] }] }); if (result.canceled) return { canceled: true }; await backups.create(result.filePath); return { saved: true } }
  if (pathname === '/backup/restore' && method === 'POST') { const result = await dialog.showOpenDialog(mainWindow, { title: 'Load OrdoCor Database Backup', properties: ['openFile'], filters: [{ name: 'OrdoCor Backup', extensions: ['ordocorbackup', 'sqlite3', 'db'] }] }); if (result.canceled) return { canceled: true }; backups.restore(result.filePaths[0]); passwords = new PasswordService(database); unlocked = !passwords.isEnabled(); return { restored: true } }
  if (pathname === '/recipe-image/select' && method === 'POST') { const result = await dialog.showOpenDialog(mainWindow, { title: 'Select Recipe Image', properties: ['openFile'], filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp'] }] }); if (result.canceled) return { canceled: true }; const filePath = result.filePaths[0]; return { name: path.basename(filePath), bytes: [...fs.readFileSync(filePath)] } }
  throw new AppError('Unknown operation.', 404)
}

ipcMain.handle('ordocor:invoke', async (_event, pathValue, options) => { try { return { ok: true, data: await route(pathValue, options) } } catch (error) { return { ok: false, status: error.status || 500, error: error.status ? error.message : 'OrdoCor could not complete that operation.' } } })
ipcMain.handle('ordocor:open-external', async (_event, url) => { if (!/^https?:\/\//i.test(url)) throw new Error('Unsupported link.'); await shell.openExternal(url); return true })

if (gotLock) {
  app.whenReady().then(() => {
    database = new OrdoCorDatabase(path.join(app.getPath('userData'), 'ordocor.sqlite3'))
    passwords = new PasswordService(database); backups = new BackupService(database, safeStorage); unlocked = !passwords.isEnabled()
    createWindow()
  }).catch(stopAfterStartupFailure)
}
app.on('second-instance', () => { if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus() } })
app.on('window-all-closed', () => app.quit())
app.on('before-quit', () => database?.close())

module.exports = { route }
