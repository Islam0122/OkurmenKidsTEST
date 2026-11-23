import { Link } from 'react-router-dom'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SKILL_GROUPS } from '../data/experience'
import { PROJECTS } from '../data/projects'
import Breadcrumbs from '../components/Breadcrumbs'
import { Card, SectionHeading, Tag } from '../components/Section'

export default function TechStackPage() {
  useDocumentMeta({
    title: 'Tech Stack — Islam Duishobaev',
    description:
      'Technologies I use: Python, Django, DRF, FastAPI, Celery, Redis, PostgreSQL, React, TypeScript, Docker. Each one linked to the projects where it is used.',
    path: '/tech-stack',
  })

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Tech Stack' }]} />
      <SectionHeading level={1} eyebrow="Stack" title="Tools and technologies" id="stack-title">
        Grouped the way I use them. Projects in the stack column show where each technology was applied in practice.
      </SectionHeading>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {SKILL_GROUPS.map((g) => (
          <Card key={g.title}>
            <h2 className="font-semibold text-ink">{g.title}</h2>
            <ul className="mt-4 flex flex-wrap gap-1.5">
              {g.items.map((i) => (
                <li key={i}><Tag>{i}</Tag></li>
              ))}
            </ul>
          </Card>
        ))}
      </div>

      <section aria-labelledby="where-used" className="mt-16">
        <h2 id="where-used" className="text-2xl font-semibold tracking-tight text-ink">Where it was applied</h2>
        <div className="mt-6 overflow-x-auto rounded-2xl border border-line">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="bg-surface-2 text-xs uppercase tracking-wider text-muted">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">Project</th>
                <th scope="col" className="px-4 py-3 font-medium">Category</th>
                <th scope="col" className="px-4 py-3 font-medium">Stack</th>
              </tr>
            </thead>
            <tbody>
              {PROJECTS.map((p) => (
                <tr key={p.slug} className="border-t border-line align-top">
                  <th scope="row" className="px-4 py-4 font-medium text-ink">
                    <Link className="underline-offset-4 hover:underline" to={`/projects/${p.slug}`}>{p.title}</Link>
                  </th>
                  <td className="px-4 py-4 text-muted">{p.category}</td>
                  <td className="px-4 py-4 text-muted">{p.stack.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
