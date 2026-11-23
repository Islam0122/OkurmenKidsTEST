import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ExternalLink, GitBranch } from 'lucide-react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { getProject } from '../data/projects'
import Breadcrumbs from '../components/Breadcrumbs'
import { Card, Tag } from '../components/Section'
import NotFoundPage from './NotFoundPage'

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section aria-labelledby={`${title.replace(/\s+/g, '-').toLowerCase()}-h`} className="mt-12">
      <h2 id={`${title.replace(/\s+/g, '-').toLowerCase()}-h`} className="text-2xl font-semibold tracking-tight text-ink">
        {title}
      </h2>
      <div className="mt-4 text-base leading-7 text-muted">{children}</div>
    </section>
  )
}

function BulletList({ items, ordered = false }: { items: string[]; ordered?: boolean }) {
  const ListTag = ordered ? 'ol' : 'ul'
  return (
    <ListTag className={`grid gap-3 ${ordered ? 'list-decimal pl-5' : ''}`}>
      {items.map((item) => (
        <li key={item} className={ordered ? 'pl-1' : 'flex gap-3'}>
          {!ordered && <span aria-hidden="true" className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />}
          <span>{item}</span>
        </li>
      ))}
    </ListTag>
  )
}

export default function ProjectDetailPage() {
  const { slug } = useParams()
  const project = getProject(slug)

  useDocumentMeta({
    title: project ? `${project.title} — Case study — Islam Duishobaev` : 'Project not found — Islam Duishobaev',
    description: project ? project.tagline : 'This project case study does not exist.',
    path: project ? `/projects/${project.slug}` : '/projects',
    noindex: !project,
    type: 'article',
  })

  if (!project) return <NotFoundPage />

  return (
    <article className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16" aria-labelledby="case-title">
      <Breadcrumbs
        items={[
          { label: 'Home', to: '/' },
          { label: 'Projects', to: '/projects' },
          { label: project.title },
        ]}
      />

      <header>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-accent">
          {project.category} · {project.period}
        </p>
        <h1 id="case-title" className="mt-3 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          {project.title}
        </h1>
        <p className="mt-5 text-lg leading-8 text-muted">{project.tagline}</p>

        <dl className="mt-8 grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs uppercase tracking-wider text-muted">My role</dt>
            <dd className="mt-1 text-sm font-medium text-ink">{project.role}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-muted">Context</dt>
            <dd className="mt-1 text-sm text-ink">{project.context}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-muted">Live demo</dt>
            <dd className="mt-1 text-sm text-ink">{project.live ?? 'Not available'}</dd>
          </div>
        </dl>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={project.github}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-accent-ink hover:opacity-90"
          >
            <GitBranch size={16} aria-hidden="true" /> View source on GitHub
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
          {project.live && (
            <a
              href={project.live}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-line px-5 py-3 text-sm font-semibold text-ink hover:border-accent"
            >
              <ExternalLink size={16} aria-hidden="true" /> Live demo
              <span className="sr-only"> (opens in a new tab)</span>
            </a>
          )}
        </div>

        <ul className="mt-6 flex flex-wrap gap-1.5" aria-label="Technologies used">
          {project.stack.map((s) => (
            <li key={s}><Tag>{s}</Tag></li>
          ))}
        </ul>
      </header>

      {project.images.length > 0 && (
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {project.images.map((img) => (
            <figure key={img.src} className="overflow-hidden rounded-2xl border border-line bg-surface">
              <img src={img.src} alt={img.alt} loading="lazy" decoding="async" className="h-auto w-full object-cover" />
            </figure>
          ))}
        </div>
      )}

      <Block title="Problem">
        <p>{project.problem}</p>
      </Block>
      <Block title="Solution">
        <p>{project.solution}</p>
      </Block>
      <Block title="My contribution">
        <p className="mb-4 text-sm">Items marked “per CV” are candidate-reported; items marked “repository-based” are visible in the code.</p>
        <BulletList items={project.contribution} />
      </Block>
      <Block title="Architecture">
        <BulletList items={project.architecture} />
      </Block>
      <Block title="Data flow">
        <BulletList items={project.dataFlow} ordered />
      </Block>
      {project.database.length > 0 && (
        <Block title="Database design">
          <BulletList items={project.database} />
        </Block>
      )}
      {project.endpoints.length > 0 && (
        <Block title="API examples">
          <div className="overflow-x-auto rounded-2xl border border-line">
            <table className="w-full min-w-[520px] text-left text-sm">
              <caption className="sr-only">Selected API endpoints</caption>
              <thead className="bg-surface-2 text-xs uppercase tracking-wider text-muted">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">Method</th>
                  <th scope="col" className="px-4 py-3 font-medium">Path</th>
                  <th scope="col" className="px-4 py-3 font-medium">Purpose</th>
                </tr>
              </thead>
              <tbody>
                {project.endpoints.map((e) => (
                  <tr key={`${e.method}-${e.path}`} className="border-t border-line">
                    <td className="px-4 py-3 font-mono text-xs text-accent">{e.method}</td>
                    <td className="px-4 py-3 font-mono text-xs text-ink">{e.path}</td>
                    <td className="px-4 py-3 text-muted">{e.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-sm">Paths are taken from the repository’s urls.py files. Request and response bodies are not documented here.</p>
        </Block>
      )}
      <Block title="Engineering challenges">
        <BulletList items={project.challenges} />
      </Block>
      {project.metrics.length > 0 && (
        <Block title="Results">
          <div className="grid gap-4 sm:grid-cols-2">
            {project.metrics.map((m) => (
              <Card key={m.label}>
                <p className="text-3xl font-semibold tracking-tight text-ink">{m.value}</p>
                <p className="mt-2 text-sm text-muted">{m.label}</p>
                <p className="mt-3 font-mono text-[11px] uppercase tracking-wider text-accent">Source: {m.source}</p>
              </Card>
            ))}
          </div>
        </Block>
      )}
      <Block title="Not verified in this write-up">
        <BulletList items={project.unavailable} />
      </Block>

      <div className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-8">
        <Link to="/projects" className="text-sm font-medium text-ink underline-offset-4 hover:underline">← All projects</Link>
        <Link to="/contact" className="text-sm font-medium text-ink underline-offset-4 hover:underline">Discuss this project →</Link>
      </div>
    </article>
  )
}
