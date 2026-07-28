/** Shared MarkdownIt instance.  Created once at module level so every
 * ChatMessage component reuses the same parser (including highlight.js). */
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch {
        /* ignore */
      }
    }
    return ''
  },
})

// Only allow http: and https: links to prevent XSS via javascript: / data: URIs
const defaultLinkRender =
  md.renderer.rules.link_open ||
  function (tokens, idx, options, _env, self) {
    return self.renderToken(tokens, idx, options)
  }
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const href = tokens[idx].attrGet('href')
  if (href) {
    const lower = href.trim().toLowerCase()
    if (!lower.startsWith('http://') && !lower.startsWith('https://')) {
      tokens[idx].attrSet('href', '')
      tokens[idx].attrSet('title', `[blocked: ${lower.slice(0, 40)}]`)
    }
  }
  return defaultLinkRender(tokens, idx, options, env, self)
}

export function renderMarkdown(text: string): string {
  return md.render(text)
}