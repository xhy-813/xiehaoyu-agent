import { ref, computed, watch, type Ref } from 'vue'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

export interface AvatarStateOptions {
  /** 聊天 store 的 isStreaming */
  isStreaming: Ref<boolean>
  /** 聊天 store 的 streamError */
  streamError: Ref<string | null>
  /** 是否有数据/图表展示 */
  hasData: Ref<boolean>
}

export function useAvatarState(opts: AvatarStateOptions) {
  const { isStreaming, streamError, hasData } = opts

  // 手动覆盖状态（用于一次性动画）
  const override = ref<AvatarState | null>(null)
  // 上一次 streaming 状态，用于检测 streaming 结束
  const wasStreaming = ref(false)

  const avatarState = computed<AvatarState>(() => {
    // 手动覆盖优先
    if (override.value) return override.value

    // 错误优先
    if (streamError.value) return 'error'

    // 流式思考中
    if (isStreaming.value) return 'thinking'

    return 'idle'
  })

  // 监听 streaming 结束 → 切换到 answering / presenting
  watch(isStreaming, (now, prev) => {
    if (prev && !now) {
      // streaming 刚刚结束
      if (streamError.value) {
        setOverride('error', 2500)
      } else if (hasData.value) {
        setOverride('presenting', 3000)
      } else {
        setOverride('answering', 2500)
      }
    }
  })

  // 监听错误出现
  watch(streamError, (err) => {
    if (err) {
      setOverride('error', 3000)
    }
  })

  /** 设置临时覆盖状态，duration 毫秒后自动清除 */
  function setOverride(state: AvatarState, duration: number) {
    override.value = state
    setTimeout(() => {
      if (override.value === state) {
        override.value = null
      }
    }, duration)
  }

  /** 手动触发一次性动画（欢迎、展示等） */
  function trigger(state: AvatarState, duration = 3000) {
    setOverride(state, duration)
  }

  /** 处理动画结束事件（非循环动画播完后切回 idle） */
  function handleAnimationEnd() {
    if (override.value && !['idle', 'thinking'].includes(override.value)) {
      override.value = null
    }
  }

  return {
    avatarState,
    trigger,
    handleAnimationEnd,
    setOverride,
  }
}