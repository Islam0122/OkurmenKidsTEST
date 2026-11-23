import { useDocumentMeta } from '../lib/useDocumentMeta'
import Breadcrumbs from '../components/Breadcrumbs'
import { Card, SectionHeading } from '../components/Section'

interface Flow {
  title: string
  note: string
  steps: { label: string; detail: string }[]
  source: { label: string; href: string }
}

const FLOWS: Flow[] = [
  {
    title: 'Okurmen testing platform: grading path',
    note: 'The request path stays fast; slow AI grading runs as a background job and writes its result back to the answer.',
    steps: [
      { label: 'React client', detail: 'Student submits an answer' },
      { label: 'Django REST API', detail: 'attempt/answer endpoint' },
      { label: 'Service layer', detail: 'Stores the answer, queues grading' },
      { label: 'Redis broker', detail: 'Celery queue' },
      { label: 'Celery worker', detail: 'grade_answer_task → GigaChat' },
      { label: 'PostgreSQL', detail: 'Score and confidence saved' },
    ],
    source: {
      label: 'backend/apps/testing/tasks.py and services/',
      href: 'https://github.com/Islam0122/OkurmenKidsTEST',
    },
  },
  {
    title: 'Access control system: request authorisation',
    note: 'Authentication and authorisation are separate steps. The RBAC check reads role rules per business element and action.',
    steps: [
      { label: 'Client', detail: 'Bearer JWT' },
      { label: 'JWT authentication', detail: 'SimpleJWT-based class' },
      { label: 'Permission check', detail: 'Roles → AccessRolesRules' },
      { label: 'Business view', detail: 'Mock products, orders, stores' },
    ],
    source: {
      label: 'apps/core and apps/access',
      href: 'https://github.com/Islam0122/AccessControlSystem',
    },
  },
  {
    title: 'JobPulse: ingestion and notification',
    note: 'Ingestion runs as periodic jobs, so the bot is not blocked by parsing. Each run is recorded for traceability.',
    steps: [
      { label: 'Telethon client', detail: 'Reads vacancy channels' },
      { label: 'hh.ru parser', detail: 'Collects postings' },
      { label: 'Vacancy store', detail: 'ParsingLog per run' },
      { label: 'Notifications', detail: 'instant / daily / weekly' },
      { label: 'Telegram bot', detail: 'Delivers to the user' },
    ],
    source: {
      label: 'backend/apps/vacancies',
      href: 'https://github.com/Islam0122/JobPulse',
    },
  },
]

function FlowDiagram({ flow }: { flow: Flow }) {
  return (
    <Card className="p-6 sm:p-8">
      <h2 className="text-xl font-semibold text-ink">{flow.title}</h2>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{flow.note}</p>
      <ol className="mt-6 flex flex-col gap-3 md:flex-row md:flex-wrap md:items-stretch md:gap-0" aria-label={`${flow.title} steps`}>
        {flow.steps.map((step, i) => (
          <li key={step.label} className="flex flex-col md:flex-row md:items-center">
            <div className="flex-1 rounded-xl border border-line bg-surface-2 px-4 py-3 md:min-w-[150px]">
              <p className="text-sm font-semibold text-ink">{step.label}</p>
              <p className="mt-1 text-xs leading-5 text-muted">{step.detail}</p>
            </div>
            {i < flow.steps.length - 1 && (
              <span aria-hidden="true" className="px-2 py-1 text-center font-mono text-accent md:px-3 md:py-0">
                <span className="md:hidden">↓</span>
                <span className="hidden md:inline">→</span>
              </span>
            )}
          </li>
        ))}
      </ol>
      <p className="mt-6 text-xs text-muted">
        Source:{' '}
        <a className="font-medium text-ink underline-offset-4 hover:underline" href={flow.source.href} target="_blank" rel="noreferrer">
          {flow.source.label}
          <span className="sr-only"> (opens in a new tab)</span>
        </a>
      </p>
    </Card>
  )
}

export default function ArchitecturePage() {
  useDocumentMeta({
    title: 'Architecture — Islam Duishobaev',
    description:
      'How the systems I built are structured: request paths, background jobs, Redis and Celery, RBAC checks and ingestion pipelines, drawn from the repositories.',
    path: '/architecture',
  })

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Architecture' }]} />
      <SectionHeading level={1} eyebrow="Systems" title="How the systems are put together" id="arch-title">
        These diagrams show the paths that exist in the code. Each one links to the source it describes. They are not production topology diagrams.
      </SectionHeading>

      <div className="grid gap-6">
        {FLOWS.map((f) => (
          <FlowDiagram key={f.title} flow={f} />
        ))}
      </div>

      <section aria-labelledby="principles" className="mt-16 grid gap-5 md:grid-cols-2">
        <Card>
          <h2 id="principles" className="text-lg font-semibold text-ink">Design principles I apply</h2>
          <ul className="mt-4 grid gap-3 text-sm leading-6 text-muted">
            <li>Keep request handling thin: views and serializers call services; services own the rules.</li>
            <li>Move slow or unreliable work (AI calls, parsing, reports) to Celery with retries and time limits.</li>
            <li>Make authorisation explicit: a named rule per resource and action, not scattered checks.</li>
            <li>Record background-job outcomes so failures can be seen and re-run.</li>
          </ul>
        </Card>
        <Card>
          <h2 className="text-lg font-semibold text-ink">Architecture write-ups</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            A separate repository holds three Django architecture notes I wrote while studying layered and domain-driven designs: a lighter layout, a middle-strength layout, and a DDD-lite variant. Each has a setup script.
          </p>
          <a
            href="https://github.com/Islam0122/django-architecture-lab"
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex text-sm font-semibold text-ink underline-offset-4 hover:underline"
          >
            Open django-architecture-lab
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
        </Card>
      </section>
    </div>
  )
}
