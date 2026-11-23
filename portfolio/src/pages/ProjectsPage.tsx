import { useMemo, useState } from 'react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { PROJECTS } from '../data/projects'
import type { ProjectCategory } from '../types'
import ProjectCard from '../components/ProjectCard'
import Breadcrumbs from '../components/Breadcrumbs'
import { EmptyState, SectionHeading } from '../components/Section'

type Filter = 'All' | ProjectCategory

const FILTERS: Filter[] = ['All', 'Professional', 'Personal', 'Learning']

export default function ProjectsPage() {
  const [filter, setFilter] = useState<Filter>('All')

  useDocumentMeta({
    title: 'Projects — Islam Duishobaev',
    description:
      'Case studies of real projects: an online testing platform with AI grading, an RBAC access-control API, a Telegram job finder and a certificate editor.',
    path: '/projects',
  })

  const visible = useMemo(
    () => (filter === 'All' ? PROJECTS : PROJECTS.filter((p) => p.category === filter)),
    [filter],
  )

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Projects' }]} />
      <SectionHeading level={1} eyebrow="Work" title="Projects and case studies" id="projects-title">
        Each case study separates what I contributed from what the team did, and labels any claim that is not verified in the repository.
      </SectionHeading>

      <div role="group" aria-label="Filter projects by category" className="mb-8 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              filter === f
                ? 'border-accent bg-accent-soft font-medium text-ink'
                : 'border-line text-muted hover:text-ink'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {visible.length > 0 ? (
        <div className="grid gap-5 md:grid-cols-2">
          {visible.map((p) => (
            <ProjectCard key={p.slug} project={p} />
          ))}
        </div>
      ) : (
        <EmptyState title="No projects in this category yet.">
          Choose “All” to see every case study.
        </EmptyState>
      )}
    </div>
  )
}
