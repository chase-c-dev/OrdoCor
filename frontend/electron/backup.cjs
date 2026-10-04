const crypto = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const Database = require('better-sqlite3')

const MAGIC = Buffer.from('ORDOCOR-ELECTRON-BACKUP-v1\n')
const REQUIRED_TABLES = ['app_settings', 'todo_items', 'calendar_items', 'investment_accounts', 'investment_stocks', 'investment_stock_watchlist', 'investment_mutual_funds', 'investment_mutual_fund_watchlist', 'investment_banking_products', 'investment_collectibles', 'investment_pipeline', 'recipes', 'recipe_categories', 'projects', 'wishlist_items', 'travel_destinations', 'vehicles', 'vehicle_maintenance', 'vehicle_wishlist', 'house_reminders', 'house_maintenance', 'house_improvements']

class BackupService {
  constructor(database, safeStorage) { this.database = database; this.safeStorage = safeStorage }

  async create(destination) {
    const temporary = path.join(os.tmpdir(), `ordocor-${crypto.randomUUID()}.sqlite3`)
    try {
      this.database.setSetting('last_backup_created_at', new Date().toISOString())
      this.database.db.pragma('wal_checkpoint(FULL)')
      await this.database.db.backup(temporary)
      const sqlite = fs.readFileSync(temporary)
      if (!this.safeStorage.isEncryptionAvailable()) throw new Error('Windows data protection is unavailable.')
      const key = crypto.randomBytes(32); const nonce = crypto.randomBytes(12)
      const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce)
      const ciphertext = Buffer.concat([cipher.update(sqlite), cipher.final()])
      const tag = cipher.getAuthTag(); const wrappedKey = this.safeStorage.encryptString(key.toString('base64'))
      const length = Buffer.alloc(4); length.writeUInt32BE(wrappedKey.length)
      fs.writeFileSync(destination, Buffer.concat([MAGIC, length, wrappedKey, nonce, tag, ciphertext]))
      return destination
    } finally { fs.rmSync(temporary, { force: true }) }
  }

  materialize(source) {
    const payload = fs.readFileSync(source)
    if (!payload.subarray(0, MAGIC.length).equals(MAGIC)) return { path: source, temporary: false }
    let offset = MAGIC.length
    const keyLength = payload.readUInt32BE(offset); offset += 4
    const wrappedKey = payload.subarray(offset, offset + keyLength); offset += keyLength
    const nonce = payload.subarray(offset, offset + 12); offset += 12
    const tag = payload.subarray(offset, offset + 16); offset += 16
    try {
      const key = Buffer.from(this.safeStorage.decryptString(wrappedKey), 'base64')
      const decipher = crypto.createDecipheriv('aes-256-gcm', key, nonce); decipher.setAuthTag(tag)
      const sqlite = Buffer.concat([decipher.update(payload.subarray(offset)), decipher.final()])
      const temporary = path.join(os.tmpdir(), `ordocor-restore-${crypto.randomUUID()}.sqlite3`)
      fs.writeFileSync(temporary, sqlite)
      return { path: temporary, temporary: true }
    } catch { throw Object.assign(new Error('This protected backup cannot be unlocked on this Windows account.'), { status: 422 }) }
  }

  validate(source) {
    if (!fs.existsSync(source)) throw Object.assign(new Error('The selected backup file does not exist.'), { status: 422 })
    const materialized = this.materialize(source)
    try {
      const candidate = new Database(materialized.path, { readonly: true, fileMustExist: true })
      const integrity = candidate.pragma('integrity_check', { simple: true })
      const tables = new Set(candidate.prepare("SELECT name FROM sqlite_master WHERE type = 'table'").all().map((row) => row.name))
      candidate.close()
      if (integrity !== 'ok') throw new Error('integrity')
      const missing = REQUIRED_TABLES.filter((table) => !tables.has(table))
      if (missing.length) throw new Error('schema')
      return materialized
    } catch (error) {
      if (materialized.temporary) fs.rmSync(materialized.path, { force: true })
      if (error.status) throw error
      throw Object.assign(new Error('The selected file is not a compatible OrdoCor backup.'), { status: 422 })
    }
  }

  restore(source) {
    const materialized = this.validate(source)
    try {
      this.database.close()
      fs.copyFileSync(materialized.path, this.database.filePath)
      for (const suffix of ['-wal', '-shm']) fs.rmSync(this.database.filePath + suffix, { force: true })
      this.database.open()
    } finally { if (materialized.temporary) fs.rmSync(materialized.path, { force: true }) }
  }
}

module.exports = { BackupService }
