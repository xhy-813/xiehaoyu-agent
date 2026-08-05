/** Shared MarkdownIt instance.  Created once at module level so every
 * ChatMessage component reuses the same parser (including highlight.js). */
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str: string, lang: string) {
    const langLabel = lang || ''
    if (lang && hljs.getLanguage(lang)) {
      try {
        const highlighted = hljs.highlight(str, { language: lang }).value
        return wrapCodeBlock(highlighted, langLabel)
      } catch {
        /* ignore */
      }
    }
    // 无语言或无高亮时，用 escapeHtml 包裹
    return wrapCodeBlock(md.utils.escapeHtml(str), langLabel)
  },
})

function wrapCodeBlock(code: string, lang: string): string {
  const langTag = lang ? `<span class="code-lang">${md.utils.escapeHtml(lang)}</span>` : ''
  const copyBtn = `<button class="code-copy-btn" onclick="
    const btn=this;
    const code=this.parentElement.querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(()=>{
      btn.innerHTML='✓';
      btn.classList.add('copied');
      setTimeout(()=>{btn.innerHTML='<svg viewBox=\\'0 0 24 24\\' width=\\'14\\' height=\\'14\\'><path fill=\\'currentColor\\' d=\\'M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z\\'/></svg>';
      btn.classList.remove('copied');
    },1500)
  " title="复制代码">
    <svg viewBox="0 0 24 24" width="14" height="14">
      <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
    </svg>
  </button>`
  return `<div class="code-block-wrapper">${langTag}${copyBtn}<pre><code>${code}</code></pre></div>`
}

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