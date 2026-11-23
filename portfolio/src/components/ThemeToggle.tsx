import { useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { applyThemePreference, readThemePreference, type ThemeChoice } from '../lib/theme'

/** Cycles: system → light → dark. The aria-label always says what the next state is. */
const NEXT: Record<ThemeChoice, ThemeChoice> = { system: 'light', light: 'dark', dark: 'system' }
const LABEL: Record<ThemeChoice, string> = {
  system: 'Theme: follows system. Switch to light theme.',
  light: 'Theme: light. Switch to dark theme.',
  dark: 'Theme: dark. Switch to system theme.',
}

export default function ThemeToggle() {
  const [choice, setChoice] = useState<ThemeChoice>(() => readThemePreference())

  function cycle() {
    const next = NEXT[choice]
    applyThemePreference(next)
    setChoice(next)
  }

  const isDark =
    choice === 'dark' ||
    (choice === 'system' && typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  return (
    <button
      type="button"
      onClick={cycle}
      aria-label={LABEL[choice]}
      title={LABEL[choice]}
      className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-line text-muted transition hover:text-ink hover:border-accent"
    >
      {isDark ? <Moon size={18} aria-hidden="true" /> : <Sun size={18} aria-hidden="true" />}
    </button>
  )
}
