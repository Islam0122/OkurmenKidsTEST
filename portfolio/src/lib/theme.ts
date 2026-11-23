export type ThemeChoice = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'theme-preference'

export function readThemePreference(): ThemeChoice {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    if (value === 'light' || value === 'dark') return value
  } catch {
    // Storage can be unavailable (private mode, blocked site data). Fall back to system.
  }
  return 'system'
}

export function applyThemePreference(choice: ThemeChoice): void {
  const root = document.documentElement
  if (choice === 'system') {
    root.removeAttribute('data-theme')
  } else {
    root.setAttribute('data-theme', choice)
  }
  try {
    if (choice === 'system') window.localStorage.removeItem(STORAGE_KEY)
    else window.localStorage.setItem(STORAGE_KEY, choice)
  } catch {
    // Ignore: the preference simply will not persist.
  }
}
