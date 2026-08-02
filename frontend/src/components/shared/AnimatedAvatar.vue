<template>
  <div
    class="animated-avatar"
    :style="{ width: size + 'px', height: size + 'px' }"
    :title="currentStateLabel"
  >
    <div ref="containerRef" class="lottie-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import lottie, { type AnimationItem } from 'lottie-web'

export type AvatarState = 'idle' | 'thinking' | 'answering' | 'welcome' | 'presenting' | 'error'

const props = withDefaults(defineProps<{
  state: AvatarState
  size?: number
}>(), {
  size: 40
})

const emit = defineEmits<{
  'animation-end': []
}>()

const containerRef = ref<HTMLElement>()
let animInstance: AnimationItem | null = null

// 需要循环播放的状态
const loopingStates: Set<AvatarState> = new Set(['idle', 'thinking'])

// 状态标签
const stateLabel: Record<AvatarState, string> = {
  idle: '待机中',
  thinking: '思考中',
  answering: '回答中',
  welcome: '欢迎',
  presenting: '展示数据',
  error: '出错了',
}

const currentStateLabel = computed(() => stateLabel[props.state])

// 动画 JSON 按状态懒加载（首屏只下载当前状态那份）
interface LottieData {
  // Lottie animation JSON structure
  [key: string]: unknown
}

const animationDataMap: Record<AvatarState, () => Promise<{ default: LottieData }>> = {
  idle: () => import('@/assets/lottie/idle.json'),
  thinking: () => import('@/assets/lottie/thinking.json'),
  answering: () => import('@/assets/lottie/answering.json'),
  welcome: () => import('@/assets/lottie/welcome.json'),
  presenting: () => import('@/assets/lottie/presenting.json'),
  error: () => import('@/assets/lottie/error.json'),
}

let loadToken = 0   // 竞态守卫：状态快速切换时丢弃过期加载

async function loadAnimation(state: AvatarState) {
  if (!containerRef.value) return
  const token = ++loadToken
  const { default: animationData } = await animationDataMap[state]()
  if (token !== loadToken || !containerRef.value) return   // 过期或已卸载

  // 销毁旧动画
  if (animInstance) {
    animInstance.destroy()
    animInstance = null
  }

  const isLooping = loopingStates.has(state)
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  animInstance = lottie.loadAnimation({
    container: containerRef.value,
    renderer: 'svg',
    loop: isLooping,
    autoplay: !reduced,
    animationData,
  })

  if (reduced) {
    animInstance.goToAndStop(0, true)   // 减少动态：静态首帧
    return
  }

  // 非循环动画播完后触发回调
  if (!isLooping) {
    animInstance.addEventListener('complete', () => {
      emit('animation-end')
    })
  }
}

onMounted(() => {
  loadAnimation(props.state)
})

watch(() => props.state, (newState, oldState) => {
  if (newState === oldState) return
  loadAnimation(newState)
})

onBeforeUnmount(() => {
  if (animInstance) {
    animInstance.destroy()
    animInstance = null
  }
})
</script>

<style scoped>
.animated-avatar {
  display: inline-block;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: rgba(100, 255, 218, 0.06);
}
.lottie-container {
  width: 100%;
  height: 100%;
}
</style>