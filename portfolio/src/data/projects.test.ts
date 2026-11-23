import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { PROJECTS, getProject } from './projects'

const PUBLIC_DIR = join(process.cwd(), 'public')

describe('project content', () => {
  it('has unique slugs and titles', () => {
    const slugs = PROJECTS.map((p) => p.slug)
    expect(new Set(slugs).size).toBe(slugs.length)
    expect(new Set(PROJECTS.map((p) => p.title)).size).toBe(PROJECTS.length)
  })

  it('links every project to a GitHub repository', () => {
    for (const p of PROJECTS) {
      expect(p.github, p.slug).toMatch(/^https:\/\/github\.com\/Islam0122\//)
    }
  })

  it('points every image at a file that exists in public/', () => {
    for (const p of PROJECTS) {
      for (const img of p.images) {
        expect(existsSync(join(PUBLIC_DIR, img.src)), `${p.slug}: ${img.src}`).toBe(true)
        expect(img.alt.length, `${p.slug}: alt text`).toBeGreaterThan(10)
      }
    }
  })

  it('states a source for every metric and never leaves a metric without a label', () => {
    for (const p of PROJECTS) {
      for (const m of p.metrics) {
        expect(['CV', 'Repository']).toContain(m.source)
        expect(m.label.length).toBeGreaterThan(0)
      }
    }
  })

  it('only lists endpoints that begin with a known API prefix', () => {
    for (const p of PROJECTS) {
      for (const e of p.endpoints) {
        expect(e.path, `${p.slug}: ${e.path}`).toMatch(/^\/(api|testing1)\//)
      }
    }
  })

  it('keeps unverified information visible for the case studies that need it', () => {
    expect(getProject('okurmen-testing-platform')?.unavailable.length).toBeGreaterThan(0)
    expect(getProject('jobpulse')?.unavailable.join(' ')).toMatch(/No automated tests/)
  })

  it('returns undefined for an unknown slug', () => {
    expect(getProject('does-not-exist')).toBeUndefined()
    expect(getProject(undefined)).toBeUndefined()
  })
})
