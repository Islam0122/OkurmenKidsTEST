import { Link } from 'react-router-dom'
import { Download } from 'lucide-react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SITE } from '../data/site'
import { EXPERIENCE, EDUCATION } from '../data/experience'
import { getProject } from '../data/projects'
import Breadcrumbs from '../components/Breadcrumbs'
import { Card, SectionHeading } from '../components/Section'

export default function ExperiencePage() {
  useDocumentMeta({
    title: 'Experience — Islam Duishobaev',
    description:
      'Work history: Full Stack developer at OKURMEN IT (2024–present) and Python Backend developer at GEEKSPRO (2023). Responsibilities and outcomes as stated on the CV.',
    path: '/experience',
  })

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Experience' }]} />
      <SectionHeading level={1} eyebrow="Experience" title="Where I have worked" id="exp-title">
        Outcomes marked “(CV)” are the candidate’s own figures and have not been independently checked.
      </SectionHeading>

      <ol className="relative grid gap-8 border-l border-line pl-6 sm:pl-8">
        {EXPERIENCE.map((job) => (
          <li key={job.company + job.period} className="relative">
            <span aria-hidden="true" className="absolute -left-[31px] top-2 h-3 w-3 rounded-full bg-accent sm:-left-[39px]" />
            <article>
              <p className="font-mono text-xs uppercase tracking-wider text-accent">{job.period} · {job.location}</p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">{job.role}</h2>
              <p className="text-base font-medium text-muted">{job.company}</p>
              <p className="mt-4 text-base leading-7 text-muted">{job.summary}</p>
              <ul className="mt-5 grid gap-3">
                {job.highlights.map((h) => (
                  <li key={h} className="flex gap-3 text-base leading-7 text-muted">
                    <span aria-hidden="true" className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    {h}
                  </li>
                ))}
              </ul>
              {job.projectSlugs.length > 0 && (
                <p className="mt-5 text-sm text-muted">
                  Related case studies:{' '}
                  {job.projectSlugs.map((slug, i) => {
                    const p = getProject(slug)
                    if (!p) return null
                    return (
                      <span key={slug}>
                        {i > 0 && ', '}
                        <Link className="font-medium text-ink underline-offset-4 hover:underline" to={`/projects/${p.slug}`}>{p.title}</Link>
                      </span>
                    )
                  })}
                </p>
              )}
            </article>
          </li>
        ))}
      </ol>

      <div className="mt-16 grid gap-5 md:grid-cols-2">
        <Card>
          <h2 className="text-lg font-semibold text-ink">Education & courses</h2>
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
          <h2 className="text-lg font-semibold text-ink">Full CV</h2>
          <p className="mt-3 text-sm text-muted">
            The full CV (Russian, PDF) has the complete work history, skills and contact details.
          </p>
          <a
            href={SITE.cvPath}
            download
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-accent-ink hover:opacity-90"
          >
            <Download size={16} aria-hidden="true" /> Download CV (PDF)
          </a>
        </Card>
      </div>
    </div>
  )
}
