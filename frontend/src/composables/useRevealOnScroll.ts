import type { Directive } from 'vue'

/** v-reveal：元素进入视口时添加 .revealed 类（配合 global.css 的 .reveal）。
 *  一次性触发；reduced-motion 时直接显示。 */

const reduced = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const observer: IntersectionObserver | null =
  typeof window !== 'undefined' && 'IntersectionObserver' in window
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              entry.target.classList.add('revealed')
              observer?.unobserve(entry.target)
            }
          }
        },
        { threshold: 0.1, rootMargin: '0px 0px -60px 0px' },
      )
    : null

export const vReveal: Directive = {
  mounted(el: HTMLElement) {
    el.classList.add('reveal')
    if (reduced() || !observer) {
      el.classList.add('revealed')
      return
    }
    observer.observe(el)
  },
  unmounted(el: HTMLElement) {
    observer?.unobserve(el)
  },
}