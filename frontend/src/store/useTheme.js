import { useEffect, useState } from 'react'
import { getSettings, resolveTheme, subscribe } from './settings.js'

// React hook returning the *resolved* theme ('light' | 'dark').
// Re-renders on settings change or OS-preference change. Used by the
// imperative chart components so they can recolour on toggle.
export function useResolvedTheme() {
  const [theme, setTheme] = useState(() => resolveTheme(getSettings().theme))

  useEffect(() => {
    const update = () => setTheme(resolveTheme(getSettings().theme))
    const unsub = subscribe(update)
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', update)
    return () => {
      unsub()
      mq.removeEventListener('change', update)
    }
  }, [])

  return theme
}
