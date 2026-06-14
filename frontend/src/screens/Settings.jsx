import { useState } from 'react'
import { motion } from 'framer-motion'
import PageTransition from '../components/PageTransition.jsx'
import { getSettings, saveSettings, INDICES, THEMES } from '../store/settings.js'

const THEME_LABELS = { light: 'Light', dark: 'Dark', system: 'System' }

function Field({ label, value, onChange, type = 'text', placeholder, hint }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-bold text-primary">{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        className="w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm font-medium text-ink outline-none focus:border-primary"
      />
      {hint && <span className="mt-1 block text-[10px] text-muted">{hint}</span>}
    </label>
  )
}

export default function Settings() {
  const [form, setForm] = useState(getSettings())
  const [saved, setSaved] = useState(false)

  const set = (key) => (val) => {
    setForm((f) => ({ ...f, [key]: val }))
    setSaved(false)
  }

  // Theme applies live (and persists immediately) for instant feedback.
  const setTheme = (t) => {
    setForm((f) => ({ ...f, theme: t }))
    saveSettings({ theme: t })
  }

  const onSave = () => {
    saveSettings(form)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <PageTransition title="Settings" subtitle="Credentials stored on this device">
      <div className="space-y-5">
        {/* Appearance */}
        <section className="card space-y-3 p-4">
          <h2 className="text-sm font-bold text-primary">Appearance</h2>
          <div className="flex gap-1 rounded-xl bg-ink/5 p-1">
            {THEMES.map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={`flex-1 rounded-lg py-2 text-xs font-bold transition ${
                  form.theme === t ? 'btn-gloss' : 'text-ink-soft'
                }`}
              >
                {THEME_LABELS[t]}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-muted">
            System follows your device's light/dark setting.
          </p>
        </section>

        {/* Angel One */}
        <section className="card space-y-3 p-4">
          <h2 className="text-sm font-bold text-primary">Angel One SmartAPI</h2>
          <Field
            label="Client ID"
            value={form.angelClientId}
            onChange={set('angelClientId')}
            placeholder="e.g. A123456"
          />
          <Field
            label="API Key"
            value={form.angelApiKey}
            onChange={set('angelApiKey')}
            type="password"
          />
          <Field
            label="PIN / MPIN"
            value={form.angelPin}
            onChange={set('angelPin')}
            type="password"
          />
          <Field
            label="TOTP Secret"
            value={form.angelTotpSecret}
            onChange={set('angelTotpSecret')}
            type="password"
            hint="Base32 secret used to auto-generate the TOTP."
          />
        </section>

        {/* Groq */}
        <section className="card space-y-3 p-4">
          <h2 className="text-sm font-bold text-primary">Groq</h2>
          <Field
            label="Groq API Key"
            value={form.groqApiKey}
            onChange={set('groqApiKey')}
            type="password"
            placeholder="gsk_…"
            hint="Powers news sentiment and the LangGraph agents (llama3-70b)."
          />
        </section>

        {/* Default index */}
        <section className="card space-y-3 p-4">
          <h2 className="text-sm font-bold text-primary">Default Index</h2>
          <div className="grid grid-cols-3 gap-2">
            {INDICES.map((i) => (
              <button
                key={i.id}
                onClick={() => set('defaultIndex')(i.id)}
                className={`rounded-xl py-2 text-xs font-bold transition ${
                  form.defaultIndex === i.id
                    ? 'btn-gloss'
                    : 'bg-bg text-ink-soft'
                }`}
              >
                {i.label}
              </button>
            ))}
          </div>
        </section>

        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onSave}
          className="w-full rounded-2xl btn-gloss py-3.5 text-base font-bold text-white shadow-card"
        >
          {saved ? 'Saved ✓' : 'Save settings'}
        </motion.button>

        <p className="px-1 pb-2 text-center text-[10px] leading-relaxed text-muted">
          All credentials live only in your browser's localStorage and are sent
          directly to the backend per request. Nothing is stored on a server.
        </p>
      </div>
    </PageTransition>
  )
}
