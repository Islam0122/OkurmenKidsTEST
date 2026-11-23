import { useEffect } from 'react'
import { SITE } from '../data/site'

interface Meta {
  title: string
  description: string
  path: string
  image?: string
  type?: 'website' | 'profile' | 'article'
  noindex?: boolean
}

function setTag(selector: string, create: () => HTMLElement, attr: string, value: string) {
  let el = document.head.querySelector<HTMLElement>(selector)
  if (!el) {
    el = create()
    document.head.appendChild(el)
  }
  el.setAttribute(attr, value)
}

/**
 * Sets per-route title, description, Open Graph and canonical metadata.
 * Canonical and absolute URLs are emitted only when VITE_SITE_URL is configured at build time.
 */
export function useDocumentMeta({ title, description, path, image, type = 'website', noindex }: Meta) {
  useEffect(() => {
    document.title = title
    setTag('meta[name="description"]', () => document.createElement('meta'), 'content', description)
    setTag('meta[property="og:title"]', () => document.createElement('meta'), 'content', title)
    setTag('meta[property="og:description"]', () => document.createElement('meta'), 'content', description)
    setTag('meta[property="og:type"]', () => document.createElement('meta'), 'content', type)
    setTag('meta[name="twitter:title"]', () => document.createElement('meta'), 'content', title)
    setTag('meta[name="twitter:description"]', () => document.createElement('meta'), 'content', description)

    if (SITE.siteUrl) {
      const url = `${SITE.siteUrl}${path}`
      setTag('meta[property="og:url"]', () => document.createElement('meta'), 'content', url)
      let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
      if (!canonical) {
        canonical = document.createElement('link')
        canonical.rel = 'canonical'
        document.head.appendChild(canonical)
      }
      canonical.href = url
    }
    if (image) {
      const absolute = SITE.siteUrl ? `${SITE.siteUrl}${image}` : image
      setTag('meta[property="og:image"]', () => document.createElement('meta'), 'content', absolute)
    }

    let robots = document.head.querySelector<HTMLMetaElement>('meta[name="robots"]')
    if (noindex) {
      if (!robots) {
        robots = document.createElement('meta')
        robots.name = 'robots'
        document.head.appendChild(robots)
      }
      robots.content = 'noindex, nofollow'
    } else if (robots) {
      robots.remove()
    }
  }, [title, description, path, image, type, noindex])
}
