<template>
  <div
    class="animated-avatar"
    :style="{ width: size + 'px', height: size + 'px' }"
    :title="stateLabel"
  >
    <div ref="containerRef" class="lottie-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import lottie, { type AnimationItem } from 'lottie-web'

import idleData from '@/assets/lottie/idle.json'
import thinkingData from '@/assets/lottie/thinking.json'
import answeringData from '@/assets/lottie/answering.json'
import welcomeData from '@/assets/lottie/welcome.json'
import presentingData from '@/assets/lottie/presenting.json'
import errorData from '@/assets/lottie/error.json'

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

const animationDataMap: Record<AvatarState, any> = {
  idle: idleData,
  thinking: thinkingData,
  answering: answeringData,
  welcome: welcomeData,
  presenting: presentingData,
  error: errorData,
}

function loadAnimation(state: AvatarState) {
  if (!containerRef.value) return

  // 销毁旧动画
  if (animInstance) {
    animInstance.destroy()
    animInstance = null
  }

  const isLooping = loopingStates.has(state)

  animInstance = lottie.loadAnimation({
    container: containerRef.value,
    renderer: 'svg',
    loop: isLooping,
    autoplay: true,
    animationData: animationDataMap[state],
  })

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
  background: rgba(99, 226, 183, 0.06);
}
.lottie-container {
  width: 100%;
  height: 100%;
}
</style>