# Xiehaoyu-Agent

基于 LLM Agent 的个人智能体与 ChatBI 系统。

- 介绍本人（RAG）
- ChatBI（Text2SQL + 自动可视化 + 结果解读）

## 技术栈

Python · LangGraph · DeepSeek · ChromaDB · SQLite · Streamlit · Plotly · HuggingFace Spaces

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env           # 填入 DEEPSEEK_API_KEY / ACCESS_CODE
streamlit run app.py
```

详见 [Xiehaoyu-Agent/overview.md](Xiehaoyu-Agent/overview.md)。
