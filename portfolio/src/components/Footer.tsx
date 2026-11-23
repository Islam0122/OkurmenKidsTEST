import { Link } from 'react-router-dom'
import { SITE } from '../data/site'

export default function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-3">
        <div>
          <p className="text-lg font-semibold text-ink">{SITE.name}</p>
          <p className="mt-2 max-w-xs text-sm text-muted">{SITE.role}. {SITE.location}.</p>
        </div>
        <nav aria-label="Footer" className="grid grid-cols-2 gap-2 text-sm">
          <Link className="text-muted hover:text-ink" to="/projects">Projects</Link>
          <Link className="text-muted hover:text-ink" to="/experience">Experience</Link>
          <Link className="text-muted hover:text-ink" to="/tech-stack">Tech Stack</Link>
          <Link className="text-muted hover:text-ink" to="/architecture">Architecture</Link>
          <Link className="text-muted hover:text-ink" to="/about">About</Link>
          <Link className="text-muted hover:text-ink" to="/contact">Contact</Link>
        </nav>
        <div className="flex flex-col gap-2 text-sm">
          <a className="text-muted hover:text-ink" href={`mailto:${SITE.email}`}>{SITE.email}</a>
          <a className="text-muted hover:text-ink" href={SITE.github} target="_blank" rel="noreferrer">GitHub · Islam0122</a>
          <a className="text-muted hover:text-ink" href={SITE.linkedin} target="_blank" rel="noreferrer">LinkedIn</a>
          <a className="text-muted hover:text-ink" href={SITE.telegramUrl} target="_blank" rel="noreferrer">Telegram · @{SITE.telegram}</a>
        </div>
      </div>
      <div className="border-t border-line">
        <p className="mx-auto max-w-6xl px-4 py-5 text-xs text-muted sm:px-6">
          © {year} {SITE.name}. Built with React, TypeScript, Vite and Tailwind CSS.
        </p>
      </div>
    </footer>
  )
}
