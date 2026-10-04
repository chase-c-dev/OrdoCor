const crypto = require('node:crypto')

const PASSWORD_ENABLED = 'password_enabled'
const PASSWORD_HASH = 'password_hash'
const PASSWORD_ITERATIONS = 'password_iterations'
const PASSWORD_PROMPT_SEEN = 'password_prompt_seen'
const PASSWORD_SALT = 'password_salt'
const ITERATIONS = 310000

class PasswordService {
  constructor(database) { this.database = database }
  hasSeenPrompt() { return this.database.getSetting(PASSWORD_PROMPT_SEEN) === '1' }
  markPromptSeen() { this.database.setSetting(PASSWORD_PROMPT_SEEN, '1') }
  isEnabled() { return this.database.getSetting(PASSWORD_ENABLED) === '1' && Boolean(this.database.getSetting(PASSWORD_HASH)) && Boolean(this.database.getSetting(PASSWORD_SALT)) }

  setPassword(password) {
    if (!password || password.length < 4) throw Object.assign(new Error('Use at least four characters.'), { status: 422 })
    const salt = crypto.randomBytes(16)
    const digest = crypto.pbkdf2Sync(password, salt, ITERATIONS, 32, 'sha256')
    this.database.setSetting(PASSWORD_SALT, salt.toString('base64'))
    this.database.setSetting(PASSWORD_HASH, digest.toString('base64'))
    this.database.setSetting(PASSWORD_ITERATIONS, String(ITERATIONS))
    this.database.setSetting(PASSWORD_ENABLED, '1')
    this.markPromptSeen()
  }

  verify(password) {
    try {
      const salt = Buffer.from(this.database.getSetting(PASSWORD_SALT), 'base64')
      const expected = Buffer.from(this.database.getSetting(PASSWORD_HASH), 'base64')
      const iterations = Number(this.database.getSetting(PASSWORD_ITERATIONS))
      const actual = crypto.pbkdf2Sync(password, salt, iterations, expected.length, 'sha256')
      return expected.length > 0 && crypto.timingSafeEqual(expected, actual)
    } catch { return false }
  }

  disable() {
    this.database.deleteSettings([PASSWORD_ENABLED, PASSWORD_HASH, PASSWORD_ITERATIONS, PASSWORD_SALT])
    this.markPromptSeen()
  }
}

module.exports = { PasswordService }
