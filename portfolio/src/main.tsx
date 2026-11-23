import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { applyThemePreference, readThemePreference } from './lib/theme'
import './index.css'

// Apply the saved theme before the first paint to avoid a flash of the wrong theme.
applyThemePreference(readThemePreference())

const rootEl = document.getElementById('root')
if (!rootEl) throw new Error('Root element #root is missing from index.html')

createRoot(rootEl).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
