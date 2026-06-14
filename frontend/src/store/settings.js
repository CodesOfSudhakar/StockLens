// Lightweight localStorage-backed settings store.
// No external state library — a tiny pub/sub keeps screens in sync.

const KEY = 'stocklens.settings'

export const INDICES = [
  { id: 'NIFTY', label: 'Nifty 50' },
  { id: 'BANKNIFTY', label: 'Bank Nifty' },
  { id: 'FINNIFTY', label: 'Fin Nifty' },
  { id: 'MIDCPNIFTY', label: 'MidCap' },
  { id: 'SENSEX', label: 'Sensex' },
]

export const THEMES = ['light', 'dark', 'system']

const DEFAULTS = {
  angelClientId: '',
  angelApiKey: '',
  angelPin: '',
  angelTotpSecret: '',
  groqApiKey: '',
  defaultIndex: 'NIFTY',
  theme: 'system',
}

const listeners = new Set()

export function getSettings() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS }
  } catch {
    return { ...DEFAULTS }
  }
}

export function saveSettings(patch) {
  const next = { ...getSettings(), ...patch }
  localStorage.setItem(KEY, JSON.stringify(next))
  listeners.forEach((fn) => fn(next))
  return next
}

export function subscribe(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

// ---- Theme ----
function prefersDark() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  )
}

// Resolve a theme setting ('light'|'dark'|'system') to 'light' | 'dark'.
export function resolveTheme(theme = getSettings().theme) {
  if (theme === 'dark') return 'dark'
  if (theme === 'light') return 'light'
  return prefersDark() ? 'dark' : 'light'
}

// Apply the resolved theme to <html> by toggling the `dark` class.
export function applyTheme(theme = getSettings().theme) {
  const resolved = resolveTheme(theme)
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('dark', resolved === 'dark')
  }
  return resolved
}

let themeInitialized = false

// Call once at startup: apply current theme and keep it in sync with the
// OS preference (only while the user is on 'system') and any settings change.
export function initTheme() {
  applyTheme()
  if (themeInitialized) return
  themeInitialized = true
  subscribe((s) => applyTheme(s.theme))
  if (typeof window !== 'undefined' && window.matchMedia) {
    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (getSettings().theme === 'system') applyTheme()
      })
  }
}

// Credentials forwarded to the backend on each request (never persisted server-side).
export function credentialHeaders() {
  const s = getSettings()
  return {
    'X-Angel-Client-Id': s.angelClientId || '',
    'X-Angel-Api-Key': s.angelApiKey || '',
    'X-Angel-Pin': s.angelPin || '',
    'X-Angel-Totp-Secret': s.angelTotpSecret || '',
    'X-Groq-Api-Key': s.groqApiKey || '',
  }
}
