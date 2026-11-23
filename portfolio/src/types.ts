export type ProjectCategory = 'Professional' | 'Personal' | 'Learning'

export interface Endpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string
  note: string
}

export interface ProjectImage {
  src: string
  alt: string
}

export interface Project {
  slug: string
  title: string
  tagline: string
  category: ProjectCategory
  /** Context of the work, exactly as far as the source material supports it. */
  context: string
  role: string
  period: string
  featured: boolean
  stack: string[]
  problem: string
  solution: string
  contribution: string[]
  architecture: string[]
  dataFlow: string[]
  database: string[]
  endpoints: Endpoint[]
  challenges: string[]
  /** Metrics are shown only when the source (CV or repository) states them. */
  metrics: { value: string; label: string; source: 'CV' | 'Repository' }[]
  /** Things that could not be verified from the sources, shown to the reader. */
  unavailable: string[]
  github: string
  live: string | null
  images: ProjectImage[]
}

export interface ExperienceEntry {
  company: string
  role: string
  period: string
  location: string
  summary: string
  highlights: string[]
  projectSlugs: string[]
}

export interface SkillGroup {
  title: string
  items: string[]
}
