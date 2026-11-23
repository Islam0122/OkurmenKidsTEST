import type { ExperienceEntry, SkillGroup } from '../types'

export const EXPERIENCE: ExperienceEntry[] = [
  {
    company: 'OKURMEN IT',
    role: 'Full Stack Developer (Python / React)',
    period: 'Jan 2024 – present',
    location: 'Bishkek, Kyrgyzstan',
    summary:
      'Development and maintenance of web products and internal IT systems for an educational organisation. Backend and front-end work, integrations and deployment.',
    highlights: [
      'LMS: backend services on Django and DRF, React interfaces for students, teachers, groups, courses and materials, plus admin tooling, analytics and reporting.',
      'Online testing platform: timed tests, automatic scoring, XP, achievements and ratings. More than 500 test sessions run (CV).',
      'AI Code Checker: GigaChat API integration with background processing through Celery and Redis; cut homework check time from several hours to roughly 20–30 minutes (CV).',
      'CRM and automation: student management tools, administrative workflows and notifications; automated up to 70% of routine administrative operations (CV).',
      'Certificate Cover Studio: template management, business logic and user interfaces.',
    ],
    projectSlugs: ['okurmen-testing-platform', 'cover-studio'],
  },
  {
    company: 'GEEKSPRO',
    role: 'Python Backend Developer',
    period: 'Oct 2023 – Dec 2023',
    location: 'Bishkek, Kyrgyzstan',
    summary:
      'Backend development for the Kolos Brewery WMS, a warehouse and finance automation system.',
    highlights: [
      'Built more than 40 REST API endpoints with Django REST Framework.',
      'Implemented product, distributor, transaction and warehouse operations, including moves between “normal” and “defect” stock statuses.',
      'Added change auditing with django-simple-history and brute-force protection with Django Axes.',
      'Generated PDF documents for invoices and returns; used database transactions for financial integrity.',
      'Optimised PostgreSQL and Django ORM queries with select_related, prefetch_related and Q objects.',
    ],
    projectSlugs: [],
  },
]

export const SKILL_GROUPS: SkillGroup[] = [
  {
    title: 'Backend',
    items: ['Python', 'Django', 'Django REST Framework', 'FastAPI', 'Flask', 'REST API design', 'Django ORM', 'SQL', 'WebSockets', 'JWT'],
  },
  {
    title: 'Frontend',
    items: ['React', 'TypeScript', 'JavaScript', 'Zustand', 'HTML5', 'CSS3', 'Tailwind CSS', 'Vite'],
  },
  {
    title: 'Data & async',
    items: ['PostgreSQL', 'Redis', 'SQLite', 'Celery', 'Celery Beat', 'Background jobs'],
  },
  {
    title: 'DevOps & tooling',
    items: ['Docker', 'Nginx', 'Gunicorn', 'Git', 'GitHub Actions', 'CI/CD', 'Railway', 'Postman'],
  },
  {
    title: 'Integrations',
    items: ['Telegram Bot API', 'Aiogram', 'Telethon', 'OpenAI API', 'GigaChat API'],
  },
  {
    title: 'Testing',
    items: ['pytest', 'pytest-django'],
  },
]

export const EDUCATION = [
  {
    title: 'International University of Kyrgyzstan',
    detail: 'Bachelor’s degree, Software Engineering. Expected graduation: 2029.',
  },
  {
    title: 'OKURMEN IT Academy',
    detail: 'Front-end development (React), 2024.',
  },
  {
    title: 'Geeks IT Academy',
    detail: 'Back-end development (Python, Django, DRF), 2023.',
  },
]

export const LANGUAGES = [
  { name: 'Kyrgyz', level: 'Native' },
  { name: 'Russian', level: 'C2' },
  { name: 'English', level: 'B1 (intermediate)' },
]
