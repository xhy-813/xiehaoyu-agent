import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Reactive media query hook.  Returns a ref that updates when the
 * query matches / no longer matches.
 */
export function useMediaQuery(query: string) {
  const matches = ref(false)

  function update() {
    matches.value = window.matchMedia(query).matches
  }

  onMounted(() => {
    update()
    window.addEventListener('resize', update)
  })
  onUnmounted(() => {
    window.removeEventListener('resize', update)
  })

  return matches
}

/**
 * Keyboard shortcut hook.  Fires *handler* when *key* is pressed.
 */
export function useEscapeKey(handler: () => void) {
  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') handler()
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}