# 方案 A：轻量头像替换

> **工时**：~0.5h | **改动文件**：2 个 | **难度**：★☆☆☆☆

## 概述

将 AI 助手头像从通用 SVG 图标替换为你的证件照，是最小成本的个人化改造。用户会在每条 AI 回复的左侧看到你的真实头像。

## 改造点

### 1. 聊天消息头像 — `ChatMessage.vue`

**当前状态**：AI 消息使用绿色圆形背景 + 地球 SVG 图标

```html
<!-- 当前代码 -->
<div v-else class="ai-avatar">
  <n-icon size="20" color="#63e2b7">
    <svg viewBox="0 0 24 24">...</svg>
  </n-icon>
</div>
```

**改造后**：使用 `n-avatar` 组件展示证件照

```html
<!-- 改造后 -->
<div v-else class="ai-avatar">
  <n-avatar :size="34" round :src="aiAvatarUrl" />
</div>
```

```ts
// script setup 中新增
import aiAvatarUrl from '@/assets/avatar.jpg'  // 从 照片/证件照.jpg 复制过来
```

**样式调整**：移除或保留 `.ai-avatar` 的背景色，头像本身已有内容。

### 2. 侧边栏 Logo — `ChatSidebar.vue`

**当前状态**：侧边栏顶部使用绿色圆角方块 + 地球 SVG 图标

```html
<!-- 当前代码 -->
<div class="sh-logo">
  <n-icon size="26" color="#63e2b7">
    <svg viewBox="0 0 24 24">...</svg>
  </n-icon>
</div>
```

**改造后**：替换为圆形头像

```html
<!-- 改造后 -->
<div class="sh-logo">
  <n-avatar :size="40" round :src="aiAvatarUrl" />
</div>
```

## 图片准备

```bash
# 1. 复制证件照到 assets 目录
cp frontend/照片/证件照.jpg frontend/src/assets/avatar.jpg

# 2. （可选）优化图片大小 — 建议裁剪为 200×200 正方形
# 可使用在线工具或用 CSS 的 object-fit: cover 处理
```

## 效果预览

```
改造前：AI 头像 = [🟢 地球图标]
改造后：AI 头像 = [📷 你的证件照]

聊天界面：
┌──────────────────────────────────────────┐
│ [📷 谢浩宇] 你好，我是谢浩宇的数字分身...  │
│                                          │
│                    你：介绍一下你自己 [👤] │
└──────────────────────────────────────────┘
```

## 优点

- 改动极小，几乎无风险
- 立即建立"真人在回答"的信任感
- 适合面试场景——HR 看到你的真实头像

## 缺点

- 仅头像变化，整体视觉提升有限
- 证件照风格偏正式，可能和暗色科技风 UI 不够融合

## 可选增强

- 给头像加一圈 `#63e2b7` 主题色描边（`box-shadow: 0 0 0 2px #63e2b7`）
- 使用 `生活照.jpg` 替代证件照，风格更自然