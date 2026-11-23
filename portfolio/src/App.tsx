import { lazy, Suspense, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import Layout from './components/Layout'

const HomePage = lazy(() => import('./pages/HomePage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'))
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage'))
const TechStackPage = lazy(() => import('./pages/TechStackPage'))
const ExperiencePage = lazy(() => import('./pages/ExperiencePage'))
const ArchitecturePage = lazy(() => import('./pages/ArchitecturePage'))
const BlogPage = lazy(() => import('./pages/BlogPage'))
const ContactPage = lazy(() => import('./pages/ContactPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function RouteFallback() {
  return (
    <div role="status" aria-live="polite" className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-24 text-muted sm:px-6">
      <span className="h-2 w-2 animate-pulse rounded-full bg-accent" aria-hidden="true" />
      Loading…
    </div>
  )
}

function ScrollToTopOnNavigate() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [pathname])
  return null
}

export default function App() {
  return (
    <>
      <ScrollToTopOnNavigate />
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:slug" element={<ProjectDetailPage />} />
            <Route path="tech-stack" element={<TechStackPage />} />
            <Route path="experience" element={<ExperiencePage />} />
            <Route path="architecture" element={<ArchitecturePage />} />
            <Route path="blog" element={<BlogPage />} />
            <Route path="contact" element={<ContactPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  )
}
