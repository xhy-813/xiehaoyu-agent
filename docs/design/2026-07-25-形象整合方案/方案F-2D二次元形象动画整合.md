# 方案 F：2D 二次元形象动画整合

> **工时**：7-11h（分阶段） | **改动文件**：6+ | **难度**：★★★☆☆
>
> 基于真实照片生成 2D 二次元角色，制作 6 种 Lottie 状态动画，替换全局头像并在多页面展示。

---

## 1. 需求概述

### 1.1 目标

将项目中的静态头像、通用图标替换为**基于真实照片生成的 2D 二次元卡通形象**，该形象具备 6 种预设动作状态，在不同交互场景下自动切换，带来"角色在思考/在回应"的生动体验。

### 1.2 设计约束

| 维度 | 要求 |
|------|------|
| 风格 | 2D 二次元，日系画风（参考《你的名字》《天气之子》） |
| 还原度 | 发型、脸型、五官比例最大程度还原真实照片 |
| 着装 | 白色/浅蓝色衬衫，商务休闲风 |
| 动画技术 | Lottie JSON，丝滑过渡 |
| 出现位置 | 聊天消息头像、侧边栏、登录页、欢迎页、个人主页 |

### 1.3 状态-场景映射

| 状态 | 触发场景 | 情绪表达 |
|------|----------|----------|
| 🟢 **待机眨眼** | 页面加载后无操作 3s | 自然放松，俏皮眨眼 |
| 🟡 **思考皱眉** | 用户发送消息后，等待 Agent 响应 | 眉头微皱，手托下巴，专注思考 |
| 🔵 **回答微笑** | Agent 返回最终答案 | 自信微笑，眼神明亮，温和专业 |
| 🟣 **欢迎挥手** | 进入登录页 / 欢迎页 | 右手抬起打招呼，开朗微笑 |
| 🟠 **展示数据** | 展示图表 / 数据表格 | 右手伸出指引手势，专业自信 |
| 🔴 **出错抱歉** | API 报错 / 超时 | 右手摸后脑勺，尴尬但可爱 |

---

## 2. 技术选型

### 2.1 推荐路径：Lottie + 图像序列

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Lottie 图像序列** | 丝滑过渡，体积小，前端生态成熟 | 位图支持有限，需额外处理 | ✅ 推荐 |
| CSS 动画 + 图片切换 | 实现简单，无依赖 | 无过渡动画，效果生硬 | 备选 |
| Live2D Cubism | 效果最好，真正的 2D 骨骼动画 | 学习曲线陡峭，需要手动拆图层 | 进阶方案 |

### 2.2 技术栈

```
AI 生图：豆包（字节跳动）
抠图：remove.bg / ClipDrop
动画制作：LottieFiles Editor / After Effects + Bodymovin 插件
前端渲染：lottie-web / vue3-lottie
```

---

## 3. 分阶段实施计划

### 阶段一：AI 生成角色基础形象

**工具**：豆包（字节跳动旗下 AI 生图工具）

**输入**：`frontend/照片/证件照.jpg`（或生活照）

**提示词**：

```
请根据这张照片生成一个2D二次元动漫风格的男性角色半身像。

【外观还原】
- 发型、脸型、五官比例最大程度还原照片中的真实人物特征
- 年龄约25岁，年轻专业人士

【着装】
- 白色衬衫，简约商务休闲风格
- 领口微开第一颗扣子，不过于正式

【构图】
- 半身像，正面朝向镜头
- 双手自然可见，方便后续制作手势动画
- 纯白色背景（#FFFFFF），方便抠图

【画风】
- 日系二次元风格，精致的赛璐珞上色
- 线条干净利落，色彩明快
- 参考《你的名字》《天气之子》的质感
- 分辨率 2048x2048 或更高

【注意】
- 角色需保持中性表情，便于后续生成不同情绪变体
- 手臂和手部完整可见，不要裁切
```

**输出物**：`base_character.png`（基础角色正面像）

**预期迭代**：2-4 次提示词调整，约 1-2 小时

---

### 阶段二：生成 6 种表情/动作变体

**方法**：将阶段一确认的基础形象图作为参考图上传，逐张追加状态描述。

#### 变体 1：待机眨眼

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 左眼闭合，右眼睁开，俏皮眨眼
- 嘴角微微上扬，自然放松的微笑
- 头部微微向左倾斜 3-5 度
【动作】
- 身体姿态与基础角色一致
- 双手自然放置
```

#### 变体 2：思考皱眉

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 双眉微微皱起，眉心有轻微皱纹
- 嘴唇轻抿，眼神看向左上方
- 眼神锐利但不过于严肃，专注思考中
【动作】
- 右手抬起，食指和拇指轻托下巴
- 左手横抱胸前，支撑右手肘
【背景】：纯白 #FFFFFF
```

#### 变体 3：回答微笑

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 嘴角上扬，露出自信但不夸张的微笑
- 眼睛微弯，眼神明亮有神采
- 眉毛舒展，整体表情温和专业
【动作】
- 身体微微前倾 5 度，显得更亲近
- 双手自然交叠放在身前
【背景】：纯白 #FFFFFF
```

#### 变体 4：欢迎挥手

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 开朗的微笑，比"回答微笑"更灿烂一些
- 眼睛弯成月牙形
【动作】
- 右手举起到头部高度，手掌张开，做挥手打招呼的动作
- 手指自然张开，不要并拢
- 左手自然放在身侧
- 身体微微向右转 5 度，营造动态感
【背景】：纯白 #FFFFFF
```

#### 变体 5：展示数据

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 自信专业的微笑
- 眼神看向左手伸出的方向
【动作】
- 左手向左侧伸出，手掌摊开朝上，做"请看"的指引手势
- 右手自然放在胸前
- 头部微微转向左侧，与手势方向一致
- 身体微微向左转 5 度
【背景】：纯白 #FFFFFF
```

#### 变体 6：出错抱歉

```
【与基础角色完全相同的角色，保持所有面部特征不变】
【表情变化】
- 尴尬但不失可爱的表情
- 眉毛呈八字形微微下垂
- 嘴角歪向一侧，似笑非笑
- 脸颊微微泛红
【动作】
- 右手抬起摸后脑勺
- 左手自然垂在身侧
- 身体微微后仰 3-5 度
【背景】：纯白 #FFFFFF
```

**输出物**：6 张角色变体 PNG（`idle.png`, `thinking.png`, `answering.png`, `welcome.png`, `presenting.png`, `error.png`）

**预期工时**：1-2 小时

---

### 阶段三：抠图与后期处理

**工具**：remove.bg（免费，单张 ≤ 25MB）或 ClipDrop（Adobe 出品）

**步骤**：

```bash
# 1. 批量抠图，去除白色背景，输出透明 PNG
#    逐个上传到 remove.bg，下载透明背景版本

# 2. 统一尺寸
#    使用 ImageMagick 或在线工具，将所有图片裁剪/缩放到统一尺寸
#    推荐：512×640（宽×高），或 600×800

# 3. 重命名
mv idle_transparent.png idle.png
mv thinking_transparent.png thinking.png
mv answering_transparent.png answering.png
mv welcome_transparent.png welcome.png
mv presenting_transparent.png presenting.png
mv error_transparent.png error.png
```

**输出物**：6 张透明背景 PNG，统一尺寸

**预期工时**：30 分钟

---

### 阶段四：Lottie 动画制作

#### 4.1 方案 A：LottieFiles Editor（推荐新手）

**地址**：https://lottiefiles.com/editor

**步骤**：

1. 注册 LottieFiles 账号
2. 创建 6 个独立动画项目
3. 每个项目导入对应的透明 PNG 作为素材
4. 为每个状态添加微动效果：

| 动画 | 关键帧效果 |
|------|-----------|
| `idle` | 轻微缩放（100%→102%→100%，循环 3s），眨眼（遮罩动画，每 4s 闭眼 0.2s） |
| `thinking` | 手指关节微动（循环 1.5s），身体微呼吸（缩放 100%→101%→100%） |
| `answering` | 头部轻微点头（旋转 ±2°，循环），嘴角上扬过渡 |
| `welcome` | 右手从静止→举起→挥手（3 次）→放下，面部表情切换 |
| `presenting` | 左手从静止→伸出→摊开→收回，眼神跟随 |
| `error` | 右手抬至脑后→摸头→放下（循环 2 次），身体微后仰 |

5. 设置帧率：24fps
6. 导出为 Lottie JSON（`.json`）

**关键技巧**：
- 每个状态时长控制在 2-4 秒
- 循环动画设置 `"lp": 0`（无限循环）或 `"lp": 1`（播放一次）
- 过渡动画（如欢迎挥手）设置 `"lp": 1`，播放完停在最后帧

#### 4.2 方案 B：After Effects + Bodymovin（专业推荐）

如具备 AE 基础，此方案效果更好：

1. 将 6 张透明 PNG 导入 AE
2. 用 Puppet Pin 工具（操控点工具）为角色添加骨骼控制点
3. 关键帧动画制作
4. 安装 Bodymovin 插件 → 导出 Lottie JSON

#### 4.3 降级方案：CSS 动画 + 图片切换

如果 Lottie 制作遇到困难，可降级为 CSS 方案：

```css
/* 呼吸动画 */
@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

/* 眨眼动画 */
@keyframes blink {
  0%, 94%, 100% { /* 睁眼 */ }
  95%, 99% { /* 闭眼 - 用 clip-path 遮挡 */ }
}

/* 淡入淡出切换 */
.state-transition {
  transition: opacity 0.4s ease-in-out;
}
```

**输出物**：6 个 Lottie JSON 文件（或 CSS 降级方案）

**预期工时**：3-5 小时（Lottie 路径，含学习成本）

---

### 阶段五：前端集成

#### 5.1 安装依赖

```bash
cd frontend
npm install lottie-web
# 或使用 Vue 3 封装
npm install vue3-lottie
```

#### 5.2 目录结构

```
frontend/src/
├── assets/
│   └── lottie/                    # Lottie 动画文件
│       ├── idle.json
│       ├── thinking.json
│       ├── answering.json
│       ├── welcome.json
│       ├── presenting.json
│       └── error.json
├── components/
│   └── shared/
│       └── AnimatedAvatar.vue     # 🆕 通用动画头像组件
└── composables/
    └── useAvatarState.ts          # 🆕 头像状态管理逻辑
```

#### 5.3 核心组件：`AnimatedAvatar.vue`

```vue
<template>
  <div class="animated-avatar" :style="{ width: size + 'px', height: size + 'px' }">
    <Vue3Lottie
      ref="lottieRef"
      :animationData="currentAnimation"
      :width="size"
      :height="size"
      :loop="currentLoop"
      :speed="1"
      @complete="onAnimationComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Vue3Lottie } from 'vue3-lottie'
import 'vue3-lottie/dist/style.css'

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

const lottieRef = ref()

const animationMap: Record<AvatarState, any> = {
  idle: idleData,
  thinking: thinkingData,
  answering: answeringData,
  welcome: welcomeData,
  presenting: presentingData,
  error: errorData,
}

// 需要循环播放的状态
const loopStates: AvatarState[] = ['idle', 'thinking']
const currentLoop = computed(() => loopStates.includes(props.state))

const currentAnimation = computed(() => animationMap[props.state])

function onAnimationComplete() {
  // 非循环动画播完后切回 idle
  if (!currentLoop.value) {
    emit('animation-end')
  }
}

// 暴露给父组件的方法
defineExpose({
  getLottieInstance: () => lottieRef.value
})
</script>

<style scoped>
.animated-avatar {
  display: inline-block;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
</style>
```

#### 5.4 状态管理：`useAvatarState.ts`

```typescript
import { ref, type Ref } from 'vue'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

export function useAvatarState() {
  const avatarState: Ref<AvatarState> = ref('idle')

  function setState(state: AvatarState) {
    avatarState.value = state
  }

  // 一次性动画播完后自动回到 idle
  function handleAnimationEnd() {
    if (['welcome', 'presenting', 'error'].includes(avatarState.value)) {
      avatarState.value = 'idle'
    }
  }

  // 与 ChatStore 的桥接
  function syncWithChat(isStreaming: boolean, hasError: boolean, hasData: boolean) {
    if (hasError) {
      avatarState.value = 'error'
    } else if (isStreaming) {
      avatarState.value = 'thinking'
    } else if (hasData) {
      avatarState.value = 'presenting'
    }
    // 否则保持当前状态或由调用方手动设置
  }

  return { avatarState, setState, handleAnimationEnd, syncWithChat }
}
```

#### 5.5 改造点清单

| 文件 | 改造内容 | 改动量 |
|------|----------|--------|
| `ChatMessage.vue` | AI 头像替换为 `AnimatedAvatar`，根据 `isStreaming` 切换状态 | ~5 行 |
| `ChatSidebar.vue` | 侧边栏 Logo 替换为 `AnimatedAvatar`（绑定 idle 状态） | ~3 行 |
| `ChatMain.vue` | 顶部欢迎区加入 `AnimatedAvatar`（welcome 状态） | ~8 行 |
| `LoginView.vue` | 登录页加入 `AnimatedAvatar`（welcome 状态） | ~8 行 |
| `WelcomeCard.vue` | 欢迎卡片加入 `AnimatedAvatar`（idle/welcome 状态） | ~5 行 |
| `chat.ts` (store) | 新增 `avatarState` 字段，在 streaming 状态变化时联动 | ~10 行 |

#### 5.6 ChatMessage.vue 改造示例

```vue
<!-- 改造前 -->
<n-avatar v-else :size="34" round :src="aiAvatarUrl" />

<!-- 改造后 -->
<AnimatedAvatar
  v-else
  :state="message.role === 'assistant' && isStreaming ? 'thinking' : 'idle'"
  :size="34"
/>
```

#### 5.7 ChatSidebar.vue 改造示例

```vue
<!-- 改造前 -->
<n-avatar :size="40" round :src="aiAvatarUrl" />

<!-- 改造后 -->
<AnimatedAvatar state="idle" :size="40" />
```

#### 5.8 LoginView.vue 改造示例

在登录表单上方添加：

```vue
<div class="login-avatar-section">
  <AnimatedAvatar
    state="welcome"
    :size="120"
    @animation-end="handleWelcomeEnd"
  />
  <h2 class="login-title">你好，我是谢浩宇的数字分身</h2>
  <p class="login-subtitle">Xiehaoyu-Agent 个人智能体工作台</p>
</div>
```

**预期工时**：2-3 小时

---

## 4. 完整文件清单

```
# 新增文件
frontend/src/assets/lottie/idle.json
frontend/src/assets/lottie/thinking.json
frontend/src/assets/lottie/answering.json
frontend/src/assets/lottie/welcome.json
frontend/src/assets/lottie/presenting.json
frontend/src/assets/lottie/error.json
frontend/src/components/shared/AnimatedAvatar.vue
frontend/src/composables/useAvatarState.ts

# 修改文件
frontend/src/components/chat/ChatMessage.vue
frontend/src/components/chat/ChatSidebar.vue
frontend/src/components/chat/ChatMain.vue
frontend/src/components/chat/WelcomeCard.vue
frontend/src/views/LoginView.vue
frontend/src/stores/chat.ts

# 中间产物（不提交到 Git）
frontend/照片/ai-generated/base_character.png
frontend/照片/ai-generated/*.png
```

---

## 5. 工时估算

| 阶段 | 内容 | 工时 |
|------|------|------|
| 一 | 豆包生成基础形象 | 1-2h |
| 二 | 生成 6 种表情变体 | 1-2h |
| 三 | 抠图与后期处理 | 0.5h |
| 四 | Lottie 动画制作 | 3-5h |
| 五 | 前端集成 | 2-3h |
| **合计** | | **7.5-12.5h** |

---

## 6. 风险与降级

| 风险 | 概率 | 降级方案 |
|------|------|----------|
| 豆包无法稳定保持角色一致性 | 中 | 换用 Midjourney `--cref` 角色参考功能，或手动画 |
| Lottie 位图动画效果不理想 | 中 | 降级为 CSS transition + 图片切换方案 |
| 6 种状态变体生图差异大 | 中 | 减少到 4 种核心状态（idle、thinking、answering、error） |
| 豆包不支持参考图生图 | 低 | 用文字详细描述面部特征，不依赖参考图 |

---

## 7. 与现有方案的关系

```
方案 A（已完成）→ 方案 F（本次）→ 方案 C（下一步）
                                        ↓
                              欢迎卡片升级 + 侧边栏信息卡
```

- 方案 A 的静态头像替换保持作为**降级兜底**（`avatar.jpg` 仍保留在 assets 中）
- 方案 F 完成后，方案 A 的 `n-avatar` 被 `AnimatedAvatar` 组件完全替代
- 方案 F 的 `AnimatedAvatar` 组件后续可复用到方案 C/D/E 中

---

## 8. 验收标准

- [ ] 豆包生成的二次元形象面部特征与真实照片高度相似
- [ ] 6 种状态动画在 Lottie 中正常播放，无卡顿
- [ ] 用户发送消息后，头像自动切换为"思考皱眉"动画
- [ ] Agent 返回结果后，头像自动切换为"回答微笑"动画
- [ ] 登录页加载时播放"欢迎挥手"动画，播完后切回"待机"
- [ ] 图表/数据展示时，头像切换为"展示数据"动画
- [ ] API 报错时，头像切换为"出错抱歉"动画
- [ ] 所有位置（聊天、侧边栏、登录页、欢迎页）头像统一
- [ ] 动画文件总大小 ≤ 500KB（6 个 JSON）