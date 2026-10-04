const fs = require('node:fs')
const path = require('node:path')
const Database = require('better-sqlite3')
const { RESOURCES, MARKET_RESOURCES } = require('./resources.cjs')

class AppError extends Error {
  constructor(message, status = 400) { super(message); this.status = status }
}

class OrdoCorDatabase {
  constructor(filePath) {
    this.filePath = filePath
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    this.open()
  }

  open() {
    this.db = new Database(this.filePath)
    this.db.pragma('foreign_keys = ON')
    this.db.pragma('journal_mode = WAL')
    this.db.exec(fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8'))
  }

  close() { if (this.db?.open) this.db.close() }

  resource(name) {
    const value = RESOURCES[name]
    if (!value) throw new AppError('Unknown resource.', 404)
    return value
  }

  list(name, parentId = null) {
    const resource = this.resource(name)
    const columns = ['id', ...resource.fields]
    if (Object.values(MARKET_RESOURCES).some(([table]) => table === resource.table)) columns.push('market_price', 'dividend_yield', 'market_updated_at')
    let where = ''
    const parameters = []
    if (parentId !== null) {
      if (!resource.parentField) throw new AppError('This resource has no parent.', 422)
      where = ` WHERE ${resource.parentField} = ?`
      parameters.push(parentId)
    }
    return this.db.prepare(`SELECT ${[...new Set(columns)].join(', ')} FROM ${resource.table}${where} ORDER BY ${resource.orderBy}`).all(...parameters)
  }

  validate(resource, payload, requireAll = false) {
    const values = Object.fromEntries(resource.fields.filter((field) => Object.hasOwn(payload, field)).map((field) => [field, payload[field]]))
    if (!Object.keys(values).length) throw new AppError('No editable fields were supplied.', 422)
    for (const field of resource.required) {
      if ((requireAll || Object.hasOwn(values, field)) && (values[field] === null || values[field] === undefined || (typeof values[field] === 'string' && !values[field].trim()))) throw new AppError(`${field.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())} is required.`, 422)
    }
    return values
  }

  create(name, payload) {
    const resource = this.resource(name)
    const values = this.validate(resource, payload, true)
    const fields = Object.keys(values)
    try {
      const result = this.db.prepare(`INSERT INTO ${resource.table} (${fields.join(', ')}) VALUES (${fields.map(() => '?').join(', ')})`).run(...fields.map((field) => values[field]))
      return this.db.prepare(`SELECT * FROM ${resource.table} WHERE id = ?`).get(result.lastInsertRowid)
    } catch (error) {
      if (String(error.code).startsWith('SQLITE_CONSTRAINT')) throw new AppError('That item already exists.', 409)
      throw error
    }
  }

  update(name, id, payload) {
    const resource = this.resource(name)
    const values = this.validate(resource, payload)
    const fields = Object.keys(values)
    const hasUpdatedAt = this.db.prepare(`PRAGMA table_info(${resource.table})`).all().some((column) => column.name === 'updated_at')
    const timestamp = hasUpdatedAt ? ', updated_at = CURRENT_TIMESTAMP' : ''
    try {
      const result = this.db.prepare(`UPDATE ${resource.table} SET ${fields.map((field) => `${field} = ?`).join(', ')}${timestamp} WHERE id = ?`).run(...fields.map((field) => values[field]), id)
      if (!result.changes) throw new AppError('Item not found.', 404)
      return this.db.prepare(`SELECT * FROM ${resource.table} WHERE id = ?`).get(id)
    } catch (error) {
      if (String(error.code).startsWith('SQLITE_CONSTRAINT')) throw new AppError('That item already exists.', 409)
      throw error
    }
  }

  remove(name, id) {
    const resource = this.resource(name)
    const result = this.db.prepare(`DELETE FROM ${resource.table} WHERE id = ?`).run(id)
    if (!result.changes) throw new AppError('Item not found.', 404)
    return { deleted: true }
  }

  upcoming() {
    const today = new Date(); const end = new Date(today); end.setDate(end.getDate() + 7)
    const iso = (value) => value.toISOString().slice(0, 10)
    return this.db.prepare('SELECT id, item_date, title, notes FROM calendar_items WHERE item_date BETWEEN ? AND ? ORDER BY item_date, title').all(iso(today), iso(end))
  }

  recipeImage(id) {
    const row = this.db.prepare('SELECT image_data, image_name FROM recipes WHERE id = ?').get(id)
    if (!row?.image_data) throw new AppError('Recipe image not found.', 404)
    const extension = path.extname(row.image_name || '').toLowerCase()
    const mime = extension === '.png' ? 'image/png' : extension === '.webp' ? 'image/webp' : 'image/jpeg'
    return { dataUrl: `data:${mime};base64,${row.image_data.toString('base64')}` }
  }

  setRecipeImage(id, bytes, name) {
    if (!bytes?.length) throw new AppError('Select a supported image file.', 422)
    if (bytes.length > 10 * 1024 * 1024) throw new AppError('Images must be 10 MB or smaller.', 413)
    const result = this.db.prepare('UPDATE recipes SET image_data = ?, image_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?').run(Buffer.from(bytes), path.basename(name || 'recipe-image'), id)
    if (!result.changes) throw new AppError('Recipe not found.', 404)
    return { uploaded: true }
  }

  getSetting(key) { return this.db.prepare('SELECT value FROM app_settings WHERE key = ?').get(key)?.value ?? null }
  setSetting(key, value) { this.db.prepare("INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP").run(key, String(value)) }
  deleteSettings(keys) { this.db.prepare(`DELETE FROM app_settings WHERE key IN (${keys.map(() => '?').join(', ')})`).run(...keys) }

  cacheHistory(symbol, prices) {
    const statement = this.db.prepare("INSERT INTO market_price_history (symbol, price_date, close_price) VALUES (?, ?, ?) ON CONFLICT(symbol, price_date) DO UPDATE SET close_price = excluded.close_price, updated_at = CURRENT_TIMESTAMP")
    this.db.transaction((rows) => rows.forEach((row) => statement.run(symbol, row.price_date, row.close_price)))(prices)
  }

  history(symbol) { return this.db.prepare('SELECT price_date, close_price FROM market_price_history WHERE symbol = ? ORDER BY price_date').all(symbol) }
}

module.exports = { AppError, OrdoCorDatabase }
