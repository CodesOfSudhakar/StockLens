import { describe, expect, it, vi } from 'vitest'
import { matchMediaMock } from '../test/setup.js'
import {
  applyTheme,
  credentialHeaders,
  getSettings,
  resolveTheme,
  saveSettings,
  subscribe,
} from './settings.js'

describe('settings store', () => {
  it('returns defaults when nothing is stored', () => {
    const s = getSettings()
    expect(s.defaultIndex).toBe('NIFTY')
    expect(s.theme).toBe('system')
    expect(s.groqApiKey).toBe('')
  })

  it('merges a patch over existing settings', () => {
    saveSettings({ defaultIndex: 'BANKNIFTY' })
    saveSettings({ groqApiKey: 'gsk_x' })
    const s = getSettings()
    expect(s.defaultIndex).toBe('BANKNIFTY') // preserved
    expect(s.groqApiKey).toBe('gsk_x')
  })

  it('persists to localStorage', () => {
    saveSettings({ angelClientId: 'A1' })
    const raw = JSON.parse(localStorage.getItem('stocklens.settings'))
    expect(raw.angelClientId).toBe('A1')
  })

  it('falls back to defaults on corrupt JSON', () => {
    localStorage.setItem('stocklens.settings', '{not valid json')
    expect(getSettings().defaultIndex).toBe('NIFTY')
  })

  it('notifies and unsubscribes listeners', () => {
    const fn = vi.fn()
    const unsub = subscribe(fn)
    saveSettings({ defaultIndex: 'SENSEX' })
    expect(fn).toHaveBeenCalledTimes(1)
    unsub()
    saveSettings({ defaultIndex: 'NIFTY' })
    expect(fn).toHaveBeenCalledTimes(1) // not called after unsubscribe
  })

  it('builds credential headers from settings', () => {
    saveSettings({ angelClientId: 'CID', groqApiKey: 'gsk_y' })
    const h = credentialHeaders()
    expect(h['X-Angel-Client-Id']).toBe('CID')
    expect(h['X-Groq-Api-Key']).toBe('gsk_y')
    expect(h['X-Angel-Pin']).toBe('') // empty, not undefined
  })
})

describe('theme resolution', () => {
  it('resolves explicit light/dark', () => {
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('resolves system to OS preference', () => {
    matchMediaMock.matches = false
    expect(resolveTheme('system')).toBe('light')
    matchMediaMock.matches = true
    expect(resolveTheme('system')).toBe('dark')
  })

  it('applyTheme toggles the dark class and returns resolved', () => {
    expect(applyTheme('dark')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(applyTheme('light')).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applyTheme system=dark adds the class', () => {
    matchMediaMock.matches = true
    applyTheme('system')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
