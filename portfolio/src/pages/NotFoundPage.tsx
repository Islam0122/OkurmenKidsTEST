import { Link } from 'react-router-dom'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { NAV_ITEMS } from '../data/site'

export default function NotFoundPage() {
  useDocumentMeta({
    title: 'Page not found — Islam Duishobaev',
    description: 'The page you are looking for does not exist. Return to the home page or browse projects.',
    path: '/404',
    noindex: true,
  })

  return (
    <div className="mx-auto max-w-3xl px-4 py-24 text-center sm:px-6">
      <p className="font-mono text-sm uppercase tracking-[0.18em] text-accent">Error 404</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">This page does not exist</h1>
      <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-muted">
        The link may be outdated, or the address may contain a typo. These pages are still here:
      </p>
      <nav aria-label="Suggested pages" className="mt-8">
        <ul className="flex flex-wrap justify-center gap-2">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <Link to={item.to} className="inline-flex rounded-full border border-line px-4 py-2 text-sm text-ink hover:border-accent">
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
