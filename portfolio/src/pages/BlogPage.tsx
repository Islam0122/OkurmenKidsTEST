import { Link } from 'react-router-dom'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SITE } from '../data/site'
import Breadcrumbs from '../components/Breadcrumbs'
import { Card, EmptyState, SectionHeading } from '../components/Section'

export default function BlogPage() {
  useDocumentMeta({
    title: 'Writing — Islam Duishobaev',
    description:
      'Articles and technical notes by Islam Duishobaev. Currently no published articles; architecture notes and source code are available on GitHub.',
    path: '/blog',
  })

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Writing' }]} />
      <SectionHeading level={1} eyebrow="Writing" title="Articles and technical notes" id="blog-title">
        I have not published articles on this site yet. Until then, the most detailed technical material is in the repositories.
      </SectionHeading>

      <EmptyState title="No articles published yet.">
        New posts will appear here when they are ready. Architecture notes and project code are already public.
      </EmptyState>

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        <Card>
          <h2 className="font-semibold text-ink">Architecture notes</h2>
          <p className="mt-2 text-sm text-muted">Three Django architecture write-ups with setup scripts.</p>
          <a className="mt-4 inline-flex text-sm font-medium text-ink underline-offset-4 hover:underline" href="https://github.com/Islam0122/django-architecture-lab" target="_blank" rel="noreferrer">
            django-architecture-lab <span className="sr-only">(opens in a new tab)</span>
          </a>
        </Card>
        <Card>
          <h2 className="font-semibold text-ink">Case studies</h2>
          <p className="mt-2 text-sm text-muted">Longer write-ups of real projects, with what is verified and what is not.</p>
          <Link className="mt-4 inline-flex text-sm font-medium text-ink underline-offset-4 hover:underline" to="/projects">Browse projects</Link>
        </Card>
        <Card className="md:col-span-2">
          <h2 className="font-semibold text-ink">Follow along on GitHub</h2>
          <p className="mt-2 text-sm text-muted">Code and commits are the most current record of what I am working on.</p>
          <a className="mt-4 inline-flex text-sm font-medium text-ink underline-offset-4 hover:underline" href={SITE.github} target="_blank" rel="noreferrer">
            github.com/Islam0122 <span className="sr-only">(opens in a new tab)</span>
          </a>
        </Card>
      </div>
    </div>
  )
}
