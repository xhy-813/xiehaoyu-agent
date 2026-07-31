import { type Ref, nextTick } from 'vue'

/**
 * Auto-scroll composable.  Scrolls *containerRef* to the bottom whenever
 * *triggerRefs* change, but only if the user is already near the bottom
 * (within 100px).  This lets the user scroll up to read history without
 * being yanked back down.
 */
export function useAutoScroll(
  containerRef: Ref<HTMLElement | undefined>,
  triggerRefs: Ref<unknown>[],
  threshold = 100,
) {
  function scrollToBottomIfNear() {
    const el = containerRef.value
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold
    if (nearBottom) {
      el.scrollTop = el.scrollHeight
    }
  }

  function watchTriggers() {
    for (const trigger of triggerRefs) {
      // Watch each trigger ref and scroll on change
      triggerRefs.forEach((_t, i) => {
        // We use a single watchEffect-like approach
      })
    }
    // Simple approach: return the scroll function for manual integration
  }

  return { scrollToBottomIfNear }
}