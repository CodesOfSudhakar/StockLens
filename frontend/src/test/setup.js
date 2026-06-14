import '@testing-library/jest-dom/vitest'
import { afterEach, beforeEach, vi } from 'vitest'

// jsdom has no matchMedia — provide a controllable mock.
// Tests can override matchMediaMock.matches before calling theme code.
export const matchMediaMock = { matches: false, listeners: new Set() }

beforeEach(() => {
  matchMediaMock.matches = false
  matchMediaMock.listeners.clear()
  localStorage.clear()
  document.documentElement.classList.remove('dark')

  vi.stubGlobal('matchMedia', (query) => ({
    matches: matchMediaMock.matches,
    media: query,
    addEventListener: (_e, fn) => matchMediaMock.listeners.add(fn),
    removeEventListener: (_e, fn) => matchMediaMock.listeners.delete(fn),
    addListener: (fn) => matchMediaMock.listeners.add(fn),
    removeListener: (fn) => matchMediaMock.listeners.delete(fn),
    dispatchEvent: () => true,
  }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})
