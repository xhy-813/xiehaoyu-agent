# Xiehaoyu-Agent

基于 LLM Agent 的个人智能体与 ChatBI 系统。

- **介绍本人**：RAG 检索个人知识库，回答面试官/HR 关于"我是谁、做过什么"的问题
- **ChatBI**：自然语言查 Olist 电商数据（Text2SQL + 自动可视化 + 结果解读）

## 技术栈

Python · LangGraph · DeepSeek · ChromaDB · SQLite · Plotly · FastAPI · Vue 3 · TypeScript · Naive UI · Nginx

## 项目结构

```
├── agent/          # LangGraph Agent 编排 (planner → tools 循环)
├── backend/        # FastAPI 后端 (SSE 流式推送, JWT 鉴权)
├── frontend/       # Vue 3 + TypeScript 前端 (Naive UI 暗色主题)
├── chatbi/         # Text2SQL 模块 (schema, 校验, few-shot)
├── rag/            # RAG 知识库检索 (ChromaDB + BGE 嵌入)
├── prompts/        # LLM Prompt 模板
├── configs/        # 全局配置
├── deploy/         # 部署配置 (Nginx, systemd)
├── tests/          # 冒烟测试
└── docs/           # 设计文档
```

## 快速开始

### 方式一：Streamlit 快速体验

```bash
python -m venv .venv
source .venv/bin/activate            # Linux/Mac
# .venv\Scripts\activate             # Windows
pip install -r requirements.txt
cp .env.example .env                 # 填入 DEEPSEEK_API_KEY / ACCESS_CODE
streamlit run app.py
```

### 方式二：Vue 3 + FastAPI 生产部署

```bash
# 后端
pip install -r requirements.txt
pip install -r backend/requirements.txt
cp .env.example .env                 # 填入 DEEPSEEK_API_KEY / ACCESS_CODE / JWT_SECRET
uvicorn backend.app.main:app --reload

# 前端
cd frontend && npm install && npm run dev
# 浏览器打开 http://localhost:5173
```

### 部署到服务器

```bash
# 参考 deploy/deploy.sh 一键部署脚本
# 适用于 Ubuntu 20.04+ / 腾讯云轻量服务器
chmod +x deploy/deploy.sh && sudo ./deploy.sh
```

## 架构

```
用户浏览器 (Vue 3 / Streamlit)
    │
    │ POST /api/chat (SSE 流式)
    ▼
FastAPI 后端 (JWT 鉴权 + 限流)
    │
    ▼
LangGraph Agent 状态机
    │
    planner (LLM 决策) ←──────────┐
    │                             │
    ├─ introduce_me (RAG 检索) ───┤
    ├─ query_data  (Text2SQL) ────┤  循环 max 5 步
    ├─ visualize   (自动画图) ────┤
    └─ explain_result (解读) ─────┘
    │
    ▼
finalize → SSE 流式返回 (答案 + 数据 + 图表 + 轨迹)
```

详见 [Xiehaoyu-Agent/overview.md](Xiehaoyu-Agent/overview.md)。