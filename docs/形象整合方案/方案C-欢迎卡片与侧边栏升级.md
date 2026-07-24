# 方案 C：欢迎卡片形象升级 + 侧边栏信息卡

> **工时**：~2h | **改动文件**：4 个 | **难度**：★★★☆☆

## 概述

在方案 A 的基础上，将欢迎卡片（WelcomeCard）和侧边栏（ChatSidebar）进行个人化升级，加入你的照片和个人信息卡片。这是性价比最高的方案——改动集中在 4 个文件，但视觉提升显著。

## 改造点

### 1. 欢迎卡片升级 — `WelcomeCard.vue`

**当前状态**：通用地球图标 + "你好，我是 Xiehaoyu-Agent" + 快捷提问卡片

**改造后**：你的照片 + 个性化问候 + 快捷提问卡片

```
┌────────────────────────────────────────────────┐
│                                                │
│         ┌──────┐                               │
│         │      │                               │
│         │ 照片 │   你好，我是谢浩宇             │
│         │      │   Xiehaoyu-Agent · 数字分身     │
│         └──────┘                               │
│                                                │
│   数据科学与大数据技术 · 吉首大学 2023 级         │
│   正在找数据分析 / 数据工程方向实习               │
│                                                │
│   ┌────────────────────────────────────────┐   │
│   │ 🌐  自我介绍 — 了解我的背景和经历       > │   │
│   │ 📊  数据分析 — 查询 Olist 电商数据      > │   │
│   │ 📁  项目经历 — 了解我做过什么项目        > │   │
│   └────────────────────────────────────────┘   │
│                                                │
└────────────────────────────────────────────────┘
```

**实现代码**：

```html
<template>
  <div class="welcome">
    <!-- 头像 + 个人信息 -->
    <div class="profile-header">
      <div class="profile-avatar-wrapper">
        <img src="@/assets/avatar.jpg" alt="谢浩宇" class="profile-avatar" />
        <div class="avatar-ring" />
      </div>
      <div class="profile-info">
        <h2 class="welcome-title">你好，我是谢浩宇</h2>
        <p class="welcome-subtitle">Xiehaoyu-Agent · 数字分身</p>
        <div class="profile-tags">
          <span class="profile-tag">数据科学与大数据技术</span>
          <span class="profile-tag">吉首大学 2023 级</span>
        </div>
        <p class="profile-status">🔍 正在找数据分析 / 数据工程方向实习</p>
      </div>
    </div>

    <!-- 快捷卡片（保持不变） -->
    <div class="quick-cards">...</div>
  </div>
</template>
```

**关键样式**：

```css
.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.profile-avatar-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.profile-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid rgba(99, 226, 183, 0.4);
  animation: ringPulse 3s ease-in-out infinite;
}

@keyframes ringPulse {
  0%, 100% { border-color: rgba(99, 226, 183, 0.3); }
  50% { border-color: rgba(99, 226, 183, 0.7); }
}

.profile-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.profile-tag {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 100px;
  background: rgba(99, 226, 183, 0.1);
  color: #63e2b7;
  border: 1px solid rgba(99, 226, 183, 0.2);
}

.profile-status {
  font-size: 0.82rem;
  color: #888;
  margin: 0.5rem 0 0;
}
```

### 2. 侧边栏信息卡升级 — `ChatSidebar.vue`

**当前状态**：Logo 图标 + 标题 + 状态网格 + 操作按钮 + 技术徽章

**改造后**：替换 Logo 为照片 + 新增个人信息区

```
┌──────────────────────────┐
│                          │
│  [📷 照片]  Xiehaoyu-Agent│
│            个人智能体工作台│
│  ─────────────────────── │
│                          │
│  📋 个人信息              │
│  ┌────────────────────┐  │
│  │ 谢浩宇              │  │
│  │ 数据科学与大数据技术  │  │
│  │ 吉首大学 · 2023 级  │  │
│  │ 📍 广州/深圳         │  │
│  └────────────────────┘  │
│                          │
│  📊 会话状态              │
│  [3 消息] [5 步骤] [就绪] │
│                          │
│  ⚡ 操作                  │
│  [🗑 清空对话]            │
│                          │
│  ─────────────────────── │
│  LangGraph DeepSeek ...  │
│  [退出登录]              │
│                          │
└──────────────────────────┘
```

**实现代码**（在 sidebar-body 顶部新增）：

```html
<!-- 个人信息卡片 — 在 sb-section 之前插入 -->
<div class="sb-section">
  <div class="sb-label">个人信息</div>
  <div class="profile-card">
    <div class="pc-avatar">
      <img src="@/assets/avatar.jpg" alt="谢浩宇" />
    </div>
    <div class="pc-info">
      <div class="pc-name">谢浩宇</div>
      <div class="pc-detail">数据科学与大数据技术</div>
      <div class="pc-detail">吉首大学 · 2023 级</div>
      <div class="pc-detail pc-location">📍 广州 / 深圳</div>
    </div>
  </div>
</div>
```

```css
.profile-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.pc-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.pc-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pc-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: #e0e0e0;
}

.pc-detail {
  font-size: 0.7rem;
  color: #777;
  line-height: 1.5;
}

.pc-location {
  color: #63e2b7;
  font-size: 0.68rem;
}
```

### 3. 聊天消息头像 — `ChatMessage.vue`

同方案 A，将 AI 头像替换为照片。

### 4. 图片准备

```bash
cp frontend/照片/证件照.jpg frontend/src/assets/avatar.jpg
```

## 优点

- 改动集中在 4 个文件，风险可控
- 欢迎卡片和侧边栏是用户最常看到的区域，曝光度高
- 个人信息自然融入 UI，不突兀
- 与方案 A 组合后，整个聊天体验都有"真人"的感觉

## 缺点

- 个人信息硬编码在组件中，后续修改需改代码
- 侧边栏在移动端默认隐藏，手机用户看不到信息卡

## 扩展建议

- 个人信息可抽到 `src/data/profile.ts` 配置文件中，方便维护
- 侧边栏个人信息卡可加一个"展开简历"按钮，点击弹出 Modal 或跳转个人主页