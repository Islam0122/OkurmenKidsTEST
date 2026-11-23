import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import type { Project } from '../types'
import { Tag } from './Section'

export default function ProjectCard({ project }: { project: Project }) {
  return (
    <article className="group relative flex flex-col rounded-2xl border border-line bg-surface p-6 transition hover:border-accent">
      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-xs uppercase tracking-wider text-accent">{project.category}</span>
        <span className="text-xs text-muted">{project.period}</span>
      </div>
      <h3 className="mt-3 text-xl font-semibold text-ink">
        <Link to={`/projects/${project.slug}`} className="after:absolute after:inset-0 after:content-['']">
          {project.title}
        </Link>
      </h3>
      <p className="mt-2 text-sm leading-6 text-muted">{project.tagline}</p>
      <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Technologies">
        {project.stack.slice(0, 6).map((s) => (
          <li key={s}>
            <Tag>{s}</Tag>
          </li>
        ))}
        {project.stack.length > 6 && <li><Tag>+{project.stack.length - 6}</Tag></li>}
      </ul>
      <p className="mt-auto flex items-center gap-1 pt-6 text-sm font-medium text-ink">
        Read case study <ArrowUpRight size={16} aria-hidden="true" className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      </p>
    </article>
  )
}
