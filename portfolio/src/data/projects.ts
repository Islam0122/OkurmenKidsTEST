import type { Project } from '../types'

/*
 * Every fact below comes from one of two sources:
 *  - the CV (CV) — claims made by the candidate, not independently verified here
 *  - the repository code/README (Repository) — checked in the source tree
 * Anything not present in those sources is listed under `unavailable`.
 */

export const PROJECTS: Project[] = [
  {
    slug: 'okurmen-testing-platform',
    title: 'Okurmen Kids Testing & Grading Platform',
    tagline:
      'Timed online tests, automatic scoring and AI-assisted grading for an educational organisation.',
    category: 'Professional',
    context:
      'Professional work at OKURMEN IT (Full Stack Developer, Jan 2024 – present). Team project. The repository is public on GitHub and contains the Django backend and a React learning front end.',
    role: 'Full Stack Developer (Python / React)',
    period: 'Jan 2024 – present',
    featured: true,
    stack: [
      'Python',
      'Django',
      'Django REST Framework',
      'Celery',
      'Redis',
      'PostgreSQL',
      'GigaChat API',
      'Telegram Bot API',
      'pandas / openpyxl',
      'React 19',
      'Vite',
      'Zustand',
    ],
    problem:
      'Checking test answers and homework by hand took hours per batch, and an online test needs timers, session control and reliable scoring when many students sit it at once.',
    solution:
      'A Django REST backend organises tests into sessions and attempts. Scoring happens in the service layer, and free-text answers are graded asynchronously through Celery tasks that call the GigaChat API. Periodic tasks expire stale sessions and retry pending regrades. Session reports go out through a Telegram integration, and questions can be imported and exported as Excel files.',
    contribution: [
      'Backend services on Django / DRF for students, teachers, groups, courses and study materials (per CV).',
      'Timed test flow: sessions, attempts, automatic result calculation, XP, achievements and ratings (per CV).',
      'Integration of AI answer checking through GigaChat with background processing via Celery and Redis (per CV).',
      'React interfaces for the learning platform (per CV). Repository contains a Vite + React 19 app with exam, quest, badge and progress-store modules.',
      'Administrative tooling, analytics and reporting (per CV).',
    ],
    architecture: [
      'Django project with domain apps: testing (models, services, API, analytics, admin tooling).',
      'Layered flow: API views and serializers → services/ (session, grading, Excel import, Telegram reports) → models.',
      'Celery workers and Beat run the asynchronous jobs; the broker and result backend are Redis (CELERY_BROKER_URL is set from the Redis URL in settings).',
      'Deployment scripts for gunicorn, the Celery worker and beat (backend/deployment/).',
    ],
    dataFlow: [
      'A student enters a test session with a key and starts an attempt.',
      'Each answer is stored through the service layer; free-text answers are queued for grading.',
      'A Celery task (grade_answer_task) calls the GigaChat checker and persists the score and confidence on the Answer.',
      'A periodic task (regrade_pending_answers_task) re-queues answers still pending.',
      'A periodic task (expire_stale_sessions_task) closes sessions that are no longer valid.',
      'send_session_report_task produces the session report that the Telegram reporting service delivers.',
    ],
    database: [
      'Test, Question, QuestionOption: the question bank, with question types, difficulty and programming language.',
      'TestSession: a time-bounded session, with a status and an access key.',
      'StudentAttempt: one student’s attempt in a session, with a status.',
      'Answer: the stored response with AI score and confidence fields (added in migration 0005).',
      'Teacher and TeacherAccess: teacher accounts and which tests they can access.',
      'Six migrations are in the repository (0001–0006).',
    ],
    endpoints: [
      { method: 'GET', path: '/api/v1/tests/', note: 'List tests (POST creates one).' },
      { method: 'POST', path: '/api/v1/sessions/create', note: 'Create a test session for a test.' },
      { method: 'POST', path: '/api/v1/sessions/enter', note: 'Enter a session with its key.' },
      { method: 'POST', path: '/api/v1/attempt/start', note: 'Start a student attempt.' },
      { method: 'POST', path: '/api/v1/attempt/answer', note: 'Submit one answer.' },
      { method: 'POST', path: '/api/v1/attempt/finish', note: 'Finish an attempt.' },
      { method: 'GET', path: '/api/v2/leaderboard/', note: 'Leaderboard endpoint (v2).' },
      { method: 'POST', path: '/testing1/import/', note: 'Upload questions from a spreadsheet for preview.' },
    ],
    challenges: [
      'Keeping slow AI grading out of the request cycle: grading runs in Celery tasks with acks_late, reject_on_worker_lost and a soft time limit, plus a periodic regrade job for answers still pending.',
      'Avoiding lost grades: _persist_grade writes the result back to the Answer record once the task completes.',
      'Making question authoring practical for teachers through Excel import with a preview step before confirmation.',
    ],
    metrics: [
      { value: '500+', label: 'test sessions run (reported on CV)', source: 'CV' },
      { value: '~70%', label: 'routine admin operations automated (reported on CV, Okurmen CRM work)', source: 'CV' },
      { value: '20–30 min', label: 'homework check time after AI checker, previously several hours (reported on CV)', source: 'CV' },
    ],
    unavailable: [
      'Live demo URL is not confirmed; no public link is included.',
      'The exact split of work between team members is not documented in the repository.',
      'No automated test-coverage figure is available for this codebase.',
      'The repository’s backend/.env is tracked in git. Its values are not reproduced here, and the file should be removed and its secrets rotated.',
    ],
    github: 'https://github.com/Islam0122/OkurmenKidsTEST',
    live: null,
    images: [
      {
        src: '/img/okurmen-platform-laptop.jpg',
        alt: 'The Okurmen Kids learning platform open on a laptop in a development workspace',
      },
    ],
  },
  {
    slug: 'access-control-system',
    title: 'Access Control System (RBAC API)',
    tagline:
      'Authentication with email OTP and JWT, plus role-based access control for a Django REST API.',
    category: 'Personal',
    context:
      'Personal project. Public repository. Built to practise authentication and authorization design, not as a commercial product.',
    role: 'Backend developer (author)',
    period: 'Not stated in the repository',
    featured: true,
    stack: [
      'Python',
      'Django',
      'Django REST Framework',
      'SimpleJWT',
      'pytest / pytest-django',
      'Docker',
      'docker-compose',
    ],
    problem:
      'Most CRUD APIs either have no permission model or bolt one on in each view. The project explores a single RBAC model that decides who can do what to which business objects.',
    solution:
      'Users register and confirm their email with a one-time code (OTP), then sign in with JWT. Roles are attached to users, and access rules are stored per business element and per action (read, create, update, delete), with separate rules for “own” and “all” objects. An admin API assigns and revokes roles. Mock business endpoints for products, orders and stores exercise the rules.',
    contribution: [
      'Designed and implemented the authentication flow, RBAC models and permission checks (repository-based).',
      'Wrote the pytest suites for authentication and RBAC permissions (64 test functions in the repository).',
      'Packaged the project with Docker and docker-compose, with a Makefile for common commands.',
    ],
    architecture: [
      'apps/users: custom User model, Role and UserRole, registration, OTP verification, login/logout, profile and soft delete.',
      'apps/access: BusinessElement and AccessRolesRules models, plus admin endpoints for roles and permission checks.',
      'apps/core: JWT authentication class and middleware, shared services and utilities.',
      'apps/business: mock product, order and store endpoints used to demonstrate enforcement.',
      'Settings split into base, development, production and testing modules.',
    ],
    dataFlow: [
      'Register → an OTP is generated with an expiry time → the user verifies it → the account is activated.',
      'Login issues a JWT; the custom authentication class resolves the user on each request.',
      'A protected endpoint checks the user’s roles against AccessRolesRules for the target business element.',
    ],
    database: [
      'User: custom auth model with otp_code and otp_expires_at for email verification.',
      'Role and UserRole: many-to-many assignment of roles to users.',
      'BusinessElement: a protected resource type (for example products or orders).',
      'AccessRolesRules: which role may perform which action on which element, including “own” vs “all” scope.',
    ],
    endpoints: [
      { method: 'POST', path: '/api/register/', note: 'Register a user; an OTP is sent.' },
      { method: 'POST', path: '/api/verify-otp/', note: 'Confirm the email with the OTP.' },
      { method: 'POST', path: '/api/login/', note: 'Obtain JWT tokens.' },
      { method: 'POST', path: '/api/logout/', note: 'End the session.' },
      { method: 'PUT', path: '/api/profile/update/', note: 'Update the profile.' },
      { method: 'DELETE', path: '/api/profile/delete/', note: 'Soft-delete the account.' },
      { method: 'POST', path: '/api/assign-role/', note: 'Assign a role (admin).' },
      { method: 'GET', path: '/api/my-permissions/', note: 'Show the current user’s permissions.' },
      { method: 'GET', path: '/api/products/', note: 'Mock business endpoint protected by RBAC.' },
    ],
    challenges: [
      'Separating “own objects” from “all objects” permissions so that one rule set can answer both.',
      'Keeping OTP verification and expiry explicit in the data model rather than in ad-hoc views.',
    ],
    metrics: [
      { value: '64', label: 'pytest test functions across the authentication and RBAC suites', source: 'Repository' },
    ],
    unavailable: [
      'No public deployment or live demo.',
      'Project timeline is not stated in the repository.',
      'The business endpoints are mock objects by design, not a real commerce domain.',
    ],
    github: 'https://github.com/Islam0122/AccessControlSystem',
    live: null,
    images: [],
  },
  {
    slug: 'jobpulse',
    title: 'JobPulse — Telegram Job Finder',
    tagline:
      'A Django backend and Telegram bot that gather vacancies from channels and job boards and deliver them to users.',
    category: 'Personal',
    context:
      'Personal project. Public repository. The README is written in Russian and English.',
    role: 'Backend developer (author)',
    period: 'Not stated in the repository',
    featured: true,
    stack: [
      'Python',
      'Django',
      'Celery',
      'Redis',
      'Telethon',
      'PostgreSQL',
      'Docker',
      'Telegram bot',
    ],
    problem:
      'Job seekers miss relevant vacancies scattered across Telegram channels and job boards, and have no feedback loop for what they have already seen.',
    solution:
      'A Telethon parser reads vacancy channels and an hh.ru parser collects postings. Vacancies are stored with parsing logs, and users get notified in instant, daily or weekly modes. Users can react to, favourite and comment on vacancies, and the admin side manages required channels and broadcasts.',
    contribution: [
      'Backend data models and parsing pipeline for vacancies, channels, notifications and reactions (repository-based).',
      'Celery and Redis configuration for asynchronous parsing and notification jobs (repository-based).',
      'Docker-based setup for development and production (per the README).',
    ],
    architecture: [
      'Django apps: users, vacancies, channels, review, resume_analysis, broadcastprompt.',
      'vacancies/services_/telethon_parser: Telegram channel client, extractor and parser.',
      'Separate configuration modules for Redis and Telethon in config/settings.',
      'A bot/ client that talks to the backend.',
    ],
    dataFlow: [
      'Telethon reads configured channels; the hh.ru parser fetches listings.',
      'Parsed content becomes Vacancy records and each run is written to ParsingLog.',
      'Matching and notification records (VacancyNotification) feed the delivery modes (instant, daily, weekly).',
    ],
    database: [
      'Vacancy: the central job record.',
      'VacancyNotification and ParsingLog: delivery and parser-run history.',
      'VacancyReaction and FavoriteVacancy: user feedback on vacancies.',
      'RequiredChannel: channels users must subscribe to; BroadcastMessage: admin broadcasts.',
      'ResumeAnalysis and Comment: profile analysis and feedback records.',
    ],
    endpoints: [],
    challenges: [
      'Parsing external sources that change structure: ParsingLog keeps a per-run trail so failures are visible.',
      'Keeping Telegram parsing and bot delivery decoupled through background jobs.',
    ],
    metrics: [],
    unavailable: [
      'No automated tests: the app test modules currently contain zero test functions.',
      'No public deployment or live bot link is included.',
      'The public API surface is not documented in this portfolio because it was not verified in this pass.',
    ],
    github: 'https://github.com/Islam0122/JobPulse',
    live: null,
    images: [],
  },
  {
    slug: 'cover-studio',
    title: 'Cover Studio — Certificate & Cover Editor',
    tagline:
      'A browser editor for A4 covers, certificates and reports with templates, layers and PDF/PNG export.',
    category: 'Professional',
    context:
      'Professional work at OKURMEN IT, listed on the CV as “Certificate Cover Studio”. Public repository.',
    role: 'Front-end and business-logic developer',
    period: 'Not stated in the repository',
    featured: true,
    stack: [
      'React 19',
      'TypeScript',
      'Vite',
      'Tailwind CSS 4',
      'Zustand',
      'Fabric.js 7',
      'jsPDF',
      'React Router 7',
      'Lucide React',
    ],
    problem:
      'Teachers and staff needed certificates, covers and reports produced in a consistent brand style without a designer for every document.',
    solution:
      'A three-column editor built on a Fabric.js canvas in exact A4 proportions. Users pick a template, adjust colours, fonts and background, edit text in place, place a logo or a stamp (the background of an uploaded stamp is removed automatically), and export to PDF or PNG.',
    contribution: [
      'Template management, business logic and user interfaces for the certificate module (per CV).',
      'Template catalogue with 12 templates in six categories, search and orientation filter (repository README).',
    ],
    architecture: [
      'Single-page React app with React Router 7 and a Zustand store for editor state.',
      'Fabric.js canvas layer for drawing, selection, transforms and text editing.',
      'Template definitions in src/templates (art, brand, build, tech) feed the gallery and the editor.',
      'Deployable as a standard Vite build with route rewrites (vercel.json), or as a hash-routed static build for hosts without rewrites.',
    ],
    dataFlow: [
      'A template is selected and copied into editor state.',
      'Fabric.js objects are updated on user actions and synchronised back to the store.',
      'Export runs in the browser: the canvas is rasterised for PNG or laid out with jsPDF for PDF.',
    ],
    database: [],
    endpoints: [],
    challenges: [
      'Keeping an exact A4 canvas responsive across screen sizes while preserving print proportions.',
      'Removing paper backgrounds from uploaded stamps so they sit cleanly on templates.',
    ],
    metrics: [
      { value: '12', label: 'templates in six categories (repository README)', source: 'Repository' },
    ],
    unavailable: [
      'No backend or database: all state lives in the browser.',
      'The exact division of work on the team is not documented.',
    ],
    github: 'https://github.com/Islam0122/cover-studio-okurmenkids',
    live: null,
    images: [
      { src: '/img/cover-studio-editor.png', alt: 'Cover Studio editor with an A4 certificate on the canvas and the left-hand data panel' },
      { src: '/img/cover-studio-gallery.png', alt: 'Cover Studio template gallery with category filters' },
    ],
  },
]

export const FEATURED_PROJECTS = PROJECTS.filter((p) => p.featured)

export function getProject(slug: string | undefined): Project | undefined {
  return PROJECTS.find((p) => p.slug === slug)
}
