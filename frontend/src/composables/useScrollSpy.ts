import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/** 滚动侦测：观察给定 id 的区块，返回当前位于视口中部的区块 id。
 *  用于左侧导航高亮（横线指示器）。无 IntersectionObserver 时恒为首个 id。 */
export function useScrollSpy(ids: string[]): Ref<string> {
  const activeId = ref(ids[0] ?? '')
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!('IntersectionObserver' in window)) return
    const sections = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null)
    if (sections.length === 0) return

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) activeId.value = entry.target.id
        }
      },
      // 视口上 30% / 下 60% 之间为"当前区块"判定带
      { rootMargin: '-30% 0px -60% 0px' },
    )
    for (const el of sections) observer.observe(el)
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })

  return activeId
}