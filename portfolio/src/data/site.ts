export const SITE = {
  name: 'Islam Duishobaev',
  shortName: 'Islam D.',
  role: 'Full Stack Developer · Python Backend',
  location: 'Bishkek, Kyrgyzstan',
  availability: 'Open to remote Full Stack and Python Backend roles (Remote / International / CIS)',
  email: 'duishobaevislam01@gmail.com',
  phone: '+996 552 325 295',
  phoneTel: '+996552325295',
  telegram: 'islam_duishobaev',
  telegramUrl: 'https://t.me/islam_duishobaev',
  github: 'https://github.com/Islam0122',
  linkedin:
    'https://www.linkedin.com/in/islam-duishobaev-492858356',
  cvPath: '/cv/Islam-Duishobaev-CV.pdf',
  portrait: '/img/islam-portrait.jpg',
  /** Optional: set VITE_SITE_URL at build time to enable canonical URLs and OG URLs. */
  siteUrl: (import.meta.env.VITE_SITE_URL as string | undefined)?.replace(/\/$/, '') ?? '',
  tagline:
    'I build backend systems in Python and Django, REST APIs, background pipelines, and the React interfaces around them.',
  summary:
    'Full Stack developer with about three years of experience building web applications, business systems, educational platforms and AI-assisted tools. Main focus: backend development in Python with Django, Django REST Framework and FastAPI, plus React and TypeScript on the front end.',
} as const

export const NAV_ITEMS = [
  { to: '/', label: 'Home' },
  { to: '/projects', label: 'Projects' },
  { to: '/experience', label: 'Experience' },
  { to: '/tech-stack', label: 'Tech Stack' },
  { to: '/architecture', label: 'Architecture' },
  { to: '/about', label: 'About' },
  { to: '/blog', label: 'Writing' },
  { to: '/contact', label: 'Contact' },
] as const
