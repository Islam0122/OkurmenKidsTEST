import type { ReactNode } from 'react'

/** level={1} for the page's main heading; the default h2 is for sections within a page. */
export function SectionHeading({
  eyebrow,
  title,
  children,
  id,
  level = 2,
}: {
  eyebrow?: string
  title: string
  children?: ReactNode
  id?: string
  level?: 1 | 2
}) {
  const Heading = level === 1 ? 'h1' : 'h2'
  return (
    <header className="mb-10 max-w-3xl">
      {eyebrow && (
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-accent">{eyebrow}</p>
      )}
      <Heading id={id} className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        {title}
      </Heading>
      {children && <div className="mt-4 text-base leading-7 text-muted">{children}</div>}
    </header>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-line bg-surface p-6 shadow-[0_1px_0_rgba(255,255,255,0.03)_inset] ${className}`}>
      {children}
    </div>
  )
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-line bg-surface-2 px-2.5 py-1 text-xs font-medium text-muted">
      {children}
    </span>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div role="status" className="rounded-2xl border border-dashed border-line p-10 text-center">
      <p className="text-lg font-semibold text-ink">{title}</p>
      {children && <div className="mt-2 text-sm text-muted">{children}</div>}
    </div>
  )
}
