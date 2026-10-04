import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { Buffer } from 'node:buffer'
import { createRequire } from 'node:module'
import { afterEach, describe, expect, it } from 'vitest'

const require = createRequire(import.meta.url)
const { BackupService } = require('../../electron/backup.cjs')
const { OrdoCorDatabase } = require('../../electron/database.cjs')
const { analystRecommendations } = require('../../electron/market.cjs')
const { PasswordService } = require('../../electron/security.cjs')

const temporaryDirectories = []

function temporaryDirectory() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'ordocor-test-'))
  temporaryDirectories.push(directory)
  return directory
}

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) fs.rmSync(directory, { recursive: true, force: true })
})

describe('desktop data services', () => {
  it('formats analyst consensus, trend counts, and weight ratings', () => {
    const recommendations = analystRecommendations({
      financialData: { recommendationKey: 'buy', recommendationMean: 1.8, numberOfAnalystOpinions: 12, targetMeanPrice: 42 },
      recommendationTrend: { trend: [{ period: '0m', strongBuy: 4, buy: 5, hold: 2, sell: 1, strongSell: 0 }] },
      upgradeDowngradeHistory: { history: [
        { epochGradeDate: new Date('2026-02-01'), firm: 'Second Research', toGrade: 'Underweight', action: 'down' },
        { epochGradeDate: new Date('2026-03-01'), firm: 'First Research', toGrade: 'Overweight', action: 'up' },
      ] },
    })
    expect(recommendations.rows).toContainEqual({ label: 'Consensus', value: 'Buy' })
    expect(recommendations.rows).toContainEqual({ label: 'Hold', value: '2' })
    expect(recommendations.rows).toContainEqual({ label: 'First Research', value: 'Overweight · Up' })
    expect(recommendations.rows).toContainEqual({ label: 'Second Research', value: 'Underweight · Down' })
    expect(recommendations.breakdown).toContainEqual({ name: 'Hold', value: 2 })
  })

  it('creates, updates, lists, and removes allowlisted resources', () => {
    const database = new OrdoCorDatabase(path.join(temporaryDirectory(), 'ordocor.sqlite3'))
    const created = database.create('todos', { title: 'Test the desktop build', is_completed: 0 })
    expect(database.list('todos')).toHaveLength(1)
    expect(database.update('todos', created.id, { is_completed: 1 }).is_completed).toBe(1)
    expect(database.remove('todos', created.id)).toEqual({ deleted: true })
    expect(database.list('todos')).toEqual([])
    database.close()
  })

  it('hashes, verifies, and disables an optional password', () => {
    const database = new OrdoCorDatabase(path.join(temporaryDirectory(), 'ordocor.sqlite3'))
    const passwords = new PasswordService(database)
    passwords.setPassword('correct horse battery staple')
    expect(passwords.isEnabled()).toBe(true)
    expect(passwords.verify('correct horse battery staple')).toBe(true)
    expect(passwords.verify('incorrect')).toBe(false)
    passwords.disable()
    expect(passwords.isEnabled()).toBe(false)
    database.close()
  })

  it('creates and restores an encrypted database backup', async () => {
    const directory = temporaryDirectory()
    const database = new OrdoCorDatabase(path.join(directory, 'ordocor.sqlite3'))
    database.create('todos', { title: 'Preserved item' })
    const safeStorage = {
      isEncryptionAvailable: () => true,
      encryptString: (value) => Buffer.from(value, 'utf8'),
      decryptString: (value) => value.toString('utf8'),
    }
    const backups = new BackupService(database, safeStorage)
    const backupPath = path.join(directory, 'backup.ordocorbackup')
    await backups.create(backupPath)
    database.create('todos', { title: 'Temporary item' })
    backups.restore(backupPath)
    expect(database.list('todos').map((item) => item.title)).toEqual(['Preserved item'])
    expect(database.getSetting('last_backup_created_at')).toBeTruthy()
    database.close()
  })
})
