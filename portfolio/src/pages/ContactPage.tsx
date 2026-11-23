import { Download, Mail, Phone, Send } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useDocumentMeta } from '../lib/useDocumentMeta'
import { SITE } from '../data/site'
import Breadcrumbs from '../components/Breadcrumbs'
import { SectionHeading } from '../components/Section'

interface Channel {
  label: string
  value: string
  href: string
  icon: LucideIcon
  external?: boolean
}

const CHANNELS: Channel[] = [
  { label: 'Email', value: SITE.email, href: `mailto:${SITE.email}`, icon: Mail },
  { label: 'Phone', value: SITE.phone, href: `tel:${SITE.phoneTel}`, icon: Phone },
  { label: 'Telegram', value: `@${SITE.telegram}`, href: SITE.telegramUrl, icon: Send, external: true },
  { label: 'LinkedIn', value: 'islam-duishobaev', href: SITE.linkedin, icon: Send, external: true },
  { label: 'GitHub', value: 'Islam0122', href: SITE.github, icon: Send, external: true },
]

export default function ContactPage() {
  useDocumentMeta({
    title: 'Contact — Islam Duishobaev',
    description:
      'Get in touch about Full Stack or Python Backend roles, or to discuss a project. Email, phone, Telegram, LinkedIn and GitHub.',
    path: '/contact',
  })

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Contact' }]} />
      <SectionHeading level={1} eyebrow="Contact" title="Let’s talk" id="contact-title">
        I am open to remote Full Stack and Python Backend roles, including international and CIS companies. The fastest way to reach me is email or Telegram.
      </SectionHeading>

      <ul className="grid gap-3 sm:grid-cols-2">
        {CHANNELS.map((c) => {
          const Icon = c.icon
          return (
            <li key={c.label}>
              <a
                href={c.href}
                target={c.external ? '_blank' : undefined}
                rel={c.external ? 'noreferrer' : undefined}
                className="flex items-center gap-4 rounded-2xl border border-line bg-surface p-5 transition hover:border-accent"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-accent-soft text-accent">
                  <Icon size={18} aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <span className="block text-xs uppercase tracking-wider text-muted">{c.label}</span>
                  <span className="block truncate font-medium text-ink">{c.value}</span>
                  {c.external && <span className="sr-only"> (opens in a new tab)</span>}
                </span>
              </a>
            </li>
          )
        })}
      </ul>

      <div className="mt-8 flex flex-wrap items-center gap-4 rounded-2xl border border-line bg-surface p-6">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ink">Prefer a document?</p>
          <p className="text-sm text-muted">The CV is available as a PDF (Russian).</p>
        </div>
        <a
          href={SITE.cvPath}
          download
          className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-accent-ink hover:opacity-90"
        >
          <Download size={16} aria-hidden="true" /> Download CV
        </a>
      </div>

      <p className="mt-8 text-sm text-muted">
        This site has no contact form. Reach me directly by email, phone or Telegram above.
      </p>
    </div>
  )
}
