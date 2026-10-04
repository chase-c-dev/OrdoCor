import { beforeEach, describe, expect, it, vi } from 'vitest'
import { displayValue, resources } from '../config/resources'

describe('resource configuration', () => {
  it('contains every main life module and formats values', () => {
    expect(resources.stocks.market).toBe(true)
    expect(resources['mutual-fund-watchlist'].title).toBe('Mutual Fund Watchlist')
    expect(displayValue({ format: 'money' }, 12.5)).toContain('$12.50')
    expect(displayValue({ type: 'select' }, 'mutual fund')).toBe('Mutual Fund')
    expect(displayValue({}, '')).toBe('—')
    expect(displayValue({}, 2026)).toBe('2026')
  })
})

describe('desktop bridge client', () => {
  beforeEach(() => {
    vi.resetModules()
    window.ordocor = { invoke: vi.fn(), openExternal: vi.fn() }
  })

  it('sends structured IPC requests and reports desktop errors', async () => {
    window.ordocor.invoke.mockResolvedValueOnce({ ok: true, data: { id: 1 } }).mockResolvedValueOnce({ ok: false, status: 422, error: 'Invalid' })
    const { api, hasSessionToken } = await import('../api')
    expect(hasSessionToken()).toBe(true)
    expect(await api('/resources/todos', { method: 'POST', body: '{}' })).toEqual({ id: 1 })
    await expect(api('/bad')).rejects.toThrow('Invalid')
    expect(window.ordocor.invoke).toHaveBeenCalledWith('/resources/todos', { method: 'POST', body: {} })
  })

  it('builds resource operations', async () => {
    window.ordocor.invoke.mockResolvedValue({ ok: true, data: [] })
    const { resourceApi } = await import('../api')
    const store = resourceApi('todos')
    await store.list(2); await store.create({ title: 'A' }); await store.update(1, { title: 'B' }); await store.remove(1)
    expect(window.ordocor.invoke).toHaveBeenCalledTimes(4)
    expect(window.ordocor.invoke).toHaveBeenNthCalledWith(1, '/resources/todos?parent_id=2', { method: 'GET', body: undefined })
  })

  it('opens native backup and external-link operations', async () => {
    window.ordocor.invoke.mockResolvedValue({ ok: true, data: { saved: true } })
    window.ordocor.openExternal.mockResolvedValue(true)
    const { downloadBackup, openExternal } = await import('../api')
    expect(await downloadBackup()).toEqual({ saved: true })
    await openExternal('https://example.com')
    expect(window.ordocor.invoke).toHaveBeenCalledWith('/backup', { method: 'POST', body: undefined })
    expect(window.ordocor.openExternal).toHaveBeenCalledWith('https://example.com')
  })

  it('requires the Electron bridge', async () => {
    delete window.ordocor
    const { api, hasSessionToken } = await import('../api')
    expect(hasSessionToken()).toBe(false)
    await expect(api('/status')).rejects.toThrow('desktop executable')
  })
})
