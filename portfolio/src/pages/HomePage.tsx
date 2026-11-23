import { Link } from 'react-router-dom'
import { ArrowRight, Download, Mail } from 'lucide-react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SITE } from '../data/site'
import { FEATURED_PROJECTS } from '../data/projects'
import { SKILL_GROUPS } from '../data/experience'
import ProjectCard from '../components/ProjectCard'
import { SectionHeading, Tag } from '../components/Section'

const FACTS = [
  { label: 'Focus', value: 'Python backend · Django · DRF · FastAPI' },
  { label: 'Front end', value: 'React · TypeScript · Vite' },
  { label: 'Experience', value: 'About 3 years (CV)' },
  { label: 'Based in', value: SITE.location },
  { label: 'Languages', value: 'Russian C2 · English B1 · Kyrgyz native' },
  { label: 'Status', value: 'Open to remote roles' },
]

export default function HomePage() {
  useDocumentMeta({
    title: 'Islam Duishobaev — Full Stack & Python Backend Developer',
    description:
      'Python backend and full stack developer from Bishkek: Django, DRF, FastAPI, React and TypeScript. Featured projects, architecture and contact.',
    path: '/',
    image: SITE.portrait,
  })

  return (
    <>
      <section aria-labelledby="hero-title" className="mx-auto max-w-6xl px-4 pb-16 pt-16 sm:px-6 sm:pt-24">
        <div className="fade-in max-w-3xl">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-accent">{SITE.role}</p>
          <h1 id="hero-title" className="mt-4 text-5xl font-semibold tracking-tight text-ink sm:text-6xl">
            {SITE.name}
          </h1>
          <p className="mt-6 text-xl leading-8 text-muted">{SITE.tagline}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/projects"
              className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-accent-ink transition hover:opacity-90"
            >
              View projects <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <a
              href={SITE.cvPath}
              download
              className="inline-flex items-center gap-2 rounded-full border border-line px-5 py-3 text-sm font-semibold text-ink transition hover:border-accent"
            >
              <Download size={16} aria-hidden="true" /> Download CV (PDF)
            </a>
            <a
              href={`mailto:${SITE.email}`}
              className="inline-flex items-center gap-2 rounded-full border border-line px-5 py-3 text-sm font-semibold text-ink transition hover:border-accent"
            >
              <Mail size={16} aria-hidden="true" /> {SITE.email}
            </a>
          </div>
          <nav aria-label="Profiles" className="mt-6 flex flex-wrap gap-4 text-sm">
            <a className="text-muted underline-offset-4 hover:text-ink hover:underline" href={SITE.github} target="_blank" rel="noreferrer">GitHub</a>
            <a className="text-muted underline-offset-4 hover:text-ink hover:underline" href={SITE.linkedin} target="_blank" rel="noreferrer">LinkedIn</a>
            <a className="text-muted underline-offset-4 hover:text-ink hover:underline" href={SITE.telegramUrl} target="_blank" rel="noreferrer">Telegram</a>
          </nav>
        </div>

        <dl className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
          {FACTS.map((f) => (
            <div key={f.label} className="bg-surface p-5">
              <dt className="font-mono text-xs uppercase tracking-wider text-muted">{f.label}</dt>
              <dd className="mt-1 text-base font-medium text-ink">{f.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="featured-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <SectionHeading eyebrow="Selected work" title="Featured projects" id="featured-title">
          Three projects that show backend design, background processing and front-end delivery. Each case study states what is verified and what is not.
        </SectionHeading>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {FEATURED_PROJECTS.map((p) => (
            <ProjectCard key={p.slug} project={p} />
          ))}
        </div>
      </section>

      <section aria-labelledby="skills-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <SectionHeading eyebrow="Core skills" title="What I work with day to day" id="skills-title" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {SKILL_GROUPS.slice(0, 3).map((g) => (
            <div key={g.title} className="rounded-2xl border border-line bg-surface p-6">
              <h3 className="font-semibold text-ink">{g.title}</h3>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {g.items.map((i) => (
                  <li key={i}><Tag>{i}</Tag></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-6 text-sm text-muted">
          <Link className="font-medium text-ink underline-offset-4 hover:underline" to="/tech-stack">See the full stack</Link> ·{' '}
          <Link className="font-medium text-ink underline-offset-4 hover:underline" to="/experience">Experience</Link>
        </p>
      </section>
    </>
  )
}
