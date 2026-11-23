// Writes dist/sitemap.xml and appends a Sitemap line to dist/robots.txt.
// Runs after `vite build`. Needs VITE_SITE_URL (for example https://example.com); without it the step is skipped,
// because a sitemap needs absolute URLs and the production domain is not configured yet.
import { existsSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs'
import { join } from 'node:path'

const siteUrl = (process.env.VITE_SITE_URL || '').replace(/\/$/, '')
const dist = join(process.cwd(), 'dist')

if (!siteUrl) {
  console.log('[sitemap] VITE_SITE_URL is not set; skipping sitemap generation.')
  process.exit(0)
}
if (!existsSync(dist)) {
  console.error('[sitemap] dist/ not found. Run `vite build` first.')
  process.exit(1)
}

// Keep in sync with the routes in src/App.tsx. Project detail pages come from the project data.
const staticRoutes = ['/', '/about', '/projects', '/tech-stack', '/experience', '/architecture', '/blog', '/contact']
const dataSource = readFileSync(join(process.cwd(), 'src', 'data', 'projects.ts'), 'utf8')
const slugs = [...dataSource.matchAll(/slug:\s*'([^']+)'/g)].map((m) => m[1])
const routes = [...staticRoutes, ...slugs.map((s) => `/projects/${s}`)]

const today = new Date().toISOString().slice(0, 10)
const urls = routes
  .map((r) => `  <url>\n    <loc>${siteUrl}${r === '/' ? '/' : r}</loc>\n    <lastmod>${today}</lastmod>\n  </url>`)
  .join('\n')

writeFileSync(
  join(dist, 'sitemap.xml'),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
)

const robotsPath = join(dist, 'robots.txt')
if (existsSync(robotsPath)) {
  appendFileSync(robotsPath, `\nSitemap: ${siteUrl}/sitemap.xml\n`)
}
console.log(`[sitemap] wrote ${routes.length} URLs to dist/sitemap.xml`)
