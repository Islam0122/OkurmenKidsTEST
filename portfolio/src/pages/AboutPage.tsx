import { Link } from 'react-router-dom'
import { Download } from 'lucide-react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SITE } from '../data/site'
import { EDUCATION, LANGUAGES } from '../data/experience'
import { Card, SectionHeading } from '../components/Section'
import Breadcrumbs from '../components/Breadcrumbs'

const WORKING_PRINCIPLES = [
  'Clear boundaries between services, and simple designs that are easy to change.',
  'Slow work moved to background jobs, so the product stays fast for the user.',
  'Measured performance: query tuning with select_related, prefetch_related and Q objects, not guesswork.',
  'Code that is tested, observable and easy to hand over. Consistency is a practice, not a mood.',
]

export default function AboutPage() {
  useDocumentMeta({
    title: 'About — Islam Duishobaev',
    description:
      'Who I am: a Full Stack developer from Bishkek with about three years of building Python backends, REST APIs and React interfaces.',
    path: '/about',
    image: SITE.portrait,
  })

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'About' }]} />

      <div className="grid gap-12 lg:grid-cols-[minmax(0,320px)_1fr]">
        <figure className="mx-auto w-full max-w-xs lg:mx-0">
          <img
            src={SITE.portrait}
            alt="Islam Duishobaev, arms crossed, in front of a branded backdrop"
            width={960}
            height={958}
            className="aspect-square w-full rounded-2xl border border-line object-cover"
            loading="eager"
            decoding="async"
          />
          <figcaption className="mt-3 text-sm text-muted">{SITE.location}</figcaption>
        </figure>

        <div>
          <SectionHeading level={1} eyebrow="About" title="Backend-first, with the front end to match" id="about-title">
            {SITE.summary}
          </SectionHeading>

          <h2 className="text-xl font-semibold text-ink">How I work</h2>
          <ul className="mt-4 grid gap-3">
            {WORKING_PRINCIPLES.map((p) => (
              <li key={p} className="flex gap-3 text-base leading-7 text-muted">
                <span aria-hidden="true" className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                {p}
              </li>
            ))}
          </ul>

          <div className="mt-10 grid gap-5 md:grid-cols-2">
            <Card>
              <h2 className="text-lg font-semibold text-ink">Education</h2>
              <ul className="mt-4 grid gap-4">
                {EDUCATION.map((e) => (
                  <li key={e.title}>
                    <p className="font-medium text-ink">{e.title}</p>
                    <p className="text-sm text-muted">{e.detail}</p>
                  </li>
                ))}
              </ul>
            </Card>
            <Card>
              <h2 className="text-lg font-semibold text-ink">Languages</h2>
              <ul className="mt-4 grid gap-3">
                {LANGUAGES.map((l) => (
                  <li key={l.name} className="flex justify-between gap-4 text-sm">
                    <span className="font-medium text-ink">{l.name}</span>
                    <span className="text-muted">{l.level}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-6 text-sm text-muted">
                Portfolio content is in English. The full CV is available in Russian.
              </p>
            </Card>
          </div>

          <div className="mt-10 flex flex-wrap gap-3">
            <a
              href={SITE.cvPath}
              download
              className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-accent-ink hover:opacity-90"
            >
              <Download size={16} aria-hidden="true" /> Download CV (PDF, Russian)
            </a>
            <Link to="/experience" className="inline-flex items-center rounded-full border border-line px-5 py-3 text-sm font-semibold text-ink hover:border-accent">
              See experience
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
