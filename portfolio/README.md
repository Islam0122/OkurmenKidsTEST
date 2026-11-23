# Islam Duishobaev — Portfolio

Personal portfolio for Python Backend / Full Stack roles. Built with React 19, TypeScript, Vite, Tailwind CSS 4 and React Router 7.

Content is typed in `src/data/` and every project fact is tagged as either **CV** (candidate-reported) or **Repository** (checked in source code). Anything that could not be verified is shown on the case-study page under “Not verified in this write-up”.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Hero, recruiter fact sheet, featured projects, core skills |
| `/about` | Profile, working principles, education, languages |
| `/projects` | All case studies with category filter |
| `/projects/:slug` | Case study: problem, solution, contribution, architecture, data flow, database, API examples, challenges, results, unverified items |
| `/experience` | Work history from the CV, education, CV download |
| `/tech-stack` | Stack grouped by area, with where each technology was used |
| `/architecture` | Request, background-job and ingestion flows, linked to source |
| `/blog` | Writing page (honest empty state until articles exist) |
| `/contact` | Email, phone, Telegram, LinkedIn, GitHub, CV |
| `*` | Custom 404 (`noindex`) |

## Commands

```bash
npm install
npm run dev         # http://localhost:5173
npm run typecheck   # tsc --noEmit
npm run lint        # eslint
npm test            # vitest (data integrity checks)
npm run build       # typecheck + vite build + sitemap (if VITE_SITE_URL is set)
npm run preview     # serve dist/ locally on :4173
```

## Configuration

Copy `.env.example` to `.env` (or set environment variables in your host) and set:

- `VITE_SITE_URL` — the production origin, for example `https://your-domain.example`. When set, the build adds canonical URLs, absolute Open Graph URLs and `dist/sitemap.xml`, and appends a `Sitemap:` line to `robots.txt`. Without it these are skipped, because the production domain is not configured yet.

## Deployment

The app uses client-side routing with `BrowserRouter`, so the host must serve `index.html` for every path:

- **Vercel**: `vercel.json` already contains the rewrite. Build command `npm run build`, output `dist`.
- **Netlify / Cloudflare Pages**: `public/_redirects` is copied into `dist/` and contains the SPA fallback.
- **Any other static host**: configure a rewrite of all paths to `/index.html`. Without it, direct URLs such as `/projects/jobpulse` return 404 from the host.

Note: the 404 page is rendered by the client, so static hosts return HTTP 200 for unknown paths unless they are configured to return 404 for them.

## Adding or editing a project

Edit `src/data/projects.ts`. Each project requires a unique `slug`, a GitHub link, and a `metrics` entry with a `source` of `CV` or `Repository`. `npm test` checks slugs, links, image paths and endpoint prefixes.

Images live in `public/img/`. The CV is `public/cv/Islam-Duishobaev-CV.pdf`; replace the file to update the download.
