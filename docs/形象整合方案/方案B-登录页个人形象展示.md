# 方案 B：登录页个人形象展示

> **工时**：~1h | **改动文件**：3 个 | **难度**：★★☆☆☆

## 概述

在登录页左侧或中央区域加入你的个人形象（全身照或生活照），让访客在进入系统前就建立"这是谢浩宇的工作台"的第一印象。

## 改造点

### 1. 登录页布局重构 — `LoginView.vue`

**当前状态**：登录页为居中单列布局，品牌区 + 登录卡片垂直排列

**改造后**：改为左右分栏布局（桌面端）

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   ┌─────────────┐    ┌──────────────────────┐    │
│   │             │    │                      │    │
│   │   [你的照片] │    │  Xiehaoyu-Agent      │    │
│   │   全身照     │    │  个人智能体·数据问答  │    │
│   │             │    │                      │    │
│   │             │    │  [🔒 访问码输入框]     │    │
│   │             │    │  [   进入工作台   ]    │    │
│   │             │    │                      │    │
│   └─────────────┘    └──────────────────────┘    │
│                                                  │
└──────────────────────────────────────────────────┘
```

**实现关键代码**：

```html
<template>
  <div class="login-wrapper">
    <!-- 背景动画保持 -->
    <div class="login-bg">...</div>

    <div class="login-content">
      <!-- 左侧：人物形象 -->
      <div class="hero-section">
        <div class="hero-image-wrapper">
          <img src="@/assets/fullbody.jpg" alt="谢浩宇" class="hero-image" />
          <div class="hero-glow" />
        </div>
        <div class="hero-tagline">
          <span class="tagline-text">谢浩宇 · 数据工程实习生</span>
        </div>
      </div>

      <!-- 右侧：品牌 + 登录表单 -->
      <div class="form-section">
        <div class="brand-section">...</div>
        <div class="card-wrapper">...</div>
      </div>
    </div>
  </div>
</template>
```

**关键样式**：

```css
.login-content {
  display: flex;
  align-items: center;
  gap: 4rem;
  max-width: 900px;
  width: 100%;
}

.hero-section {
  flex: 0 0 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-image-wrapper {
  position: relative;
  width: 280px;
  height: 380px;
  border-radius: 24px;
  overflow: hidden;
  border: 2px solid rgba(99, 226, 183, 0.2);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 30%, rgba(99, 226, 183, 0.15) 0%, transparent 70%);
}

.form-section {
  flex: 1;
  max-width: 420px;
}

/* 移动端：回退为垂直居中布局 */
@media (max-width: 768px) {
  .login-content {
    flex-direction: column;
    gap: 2rem;
  }
  .hero-section {
    flex: 0 0 auto;
  }
  .hero-image-wrapper {
    width: 160px;
    height: 200px;
    border-radius: 50%;  /* 移动端变成圆形头像 */
  }
}
```

### 2. 图片准备

```bash
# 使用全身照
cp frontend/照片/全身照.jpg frontend/src/assets/fullbody.jpg

# 或使用生活照（如果觉得全身照太正式）
cp frontend/照片/生活照.jpg frontend/src/assets/hero-photo.jpg
```

### 3. 路由守卫（可选）

如果希望未登录用户也能看到个人形象，无需改动路由。当前 `/login` 路由已设置 `meta: { guest: true }`。

## 效果预览

```
桌面端：左右分栏，你的照片在左侧，品牌和登录框在右侧
平板端：上下布局，照片变成圆形头像居中
手机端：照片隐藏或缩小，保持简洁登录体验
```

## 优点

- 第一印象强烈，登录页即建立个人品牌
- 面试场景：HR 打开链接就看见你的形象
- 和现有暗色科技风背景形成"人+科技"的对比

## 缺点

- 全身照要处理透明背景或与暗色背景协调
- 左右分栏在移动端需要回退，增加响应式逻辑
- 改动中等，需测试登录页在各种屏幕下的表现

## 图片优化建议

- 全身照建议抠图去背景（PNG 透明），或使用渐变遮罩与暗色背景融合
- 图片压缩至 100KB 以内，避免首屏加载过慢
- 可添加 CSS `filter: brightness(1.05) contrast(1.05)` 微调