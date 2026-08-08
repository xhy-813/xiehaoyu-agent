# API Embedding 改造方案

> 将 RAG 模块从本地 BGE-large 模型切换到智谱 AI `embedding-3` API，消除 ~1.3 GB 常驻内存占用。

## 背景

| 项目 | 改造前 | 改造后 |
|---|---|---|
| Embedding 方式 | 本地 `BAAI/bge-large-zh-v1.5` | 智谱 AI `embedding-3` API |
| 服务器内存占用 | ~1.3 GB（模型常驻） | ~0 MB（无本地模型） |
| 向量维度 | 1024 | 1024（可配置） |
| 费用 | 无 | ¥0.5/百万 token（约 ¥0.15/月） |
| 依赖 | `sentence-transformers`, `torch` | `openai`（已有） |

---

## 涉及改动的文件

### 1. `rag/constants.py` — 核心

新增 `_ZhipuEmbeddingFunction` 类（实现 ChromaDB `EmbeddingFunction` 协议）和 `get_embedding_function()` 工厂函数。

```python
def get_embedding_function():
    """根据 EMBED_API_KEY 环境变量自动选择 API 模式或本地 BGE 降级。"""
    api_key = os.getenv("EMBED_API_KEY", "")
    if api_key:
        return _ZhipuEmbeddingFunction(api_key=api_key, ...)
    # 降级：本地 BGE-large
    from chromadb.utils import embedding_functions
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
```

**关键实现细节：**
- 使用已有的 `openai` 包调用智谱 OpenAI 兼容接口
- 批量上限 64 条/次（API 限制），自动分批
- 按 `index` 保序，确保 ChromaDB 内向量与文本对应正确

### 2. `rag/retriever.py` — 2 行替换

```python
# 改前
from chromadb.utils import embedding_functions
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

# 改后
from rag.constants import COLLECTION, get_embedding_function
ef = get_embedding_function()
```

### 3. `rag/ingest.py` — 2 行替换（同上）

同时移除了 `HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` 强制设置（API 模式无需 HuggingFace 访问）。

### 4. `.env` / `.env.example` — 新增 4 个环境变量

```bash
# 填入后启用 API 模式；留空则自动降级到本地 BGE
EMBED_API_KEY=your_zhipuai_api_key_here
EMBED_API_BASE=https://open.bigmodel.cn/api/paas/v4
EMBED_MODEL_NAME=embedding-3
EMBED_DIMENSIONS=1024   # 可选：256 / 512 / 1024 / 2048
```

---

## 切换流程

### 启用 API 模式

1. 在 `.env` 填入 `EMBED_API_KEY`（已完成）
2. 重建知识库（**向量空间不同，必须重建**）：

```bash
python -m rag.ingest --src data/知识库 --db rag/data/chroma --force
```

3. 验证：

```bash
python -c "
from rag.retriever import retrieve
hits = retrieve('介绍一下你自己', top_k=3)
for h in hits:
    print(f'{h.source} (sim={h.similarity:.3f}): {h.content[:60]}...')
"
```

### 降级回本地模型

注释掉 `.env` 中的 `EMBED_API_KEY`，重建知识库：

```bash
# .env：注释掉 EMBED_API_KEY=...
python -m rag.ingest --src data/知识库 --db rag/data/chroma --force
```

---

## 智谱 AI embedding-3 参数说明

| 参数 | 值 | 说明 |
|---|---|---|
| 接口地址 | `https://open.bigmodel.cn/api/paas/v4/embeddings` | OpenAI 兼容 |
| 认证方式 | Bearer Token | `Authorization: Bearer <API_KEY>` |
| 单条最大 | 3072 tokens | |
| 批量最大 | 64 条/次 | |
| 向量维度 | 256 / 512 / 1024 / 2048 | 默认 2048，本项目用 **1024**（见下方说明） |
| 价格 | ¥0.5 / 百万 tokens | |
| 并发（V0） | 50 | 免费账户 |

---

## 向量维度选择说明

embedding-3 API 默认返回 2048 维，本项目配置为 **1024 维**，原因如下：

1. **与原 BGE-large 保持一致**：改造前本地 BGE-large-zh-v1.5 输出维度即为 1024，保持一致可降低潜在兼容风险
2. **语料复杂度低**：RAG 语料为个人简历和项目介绍，文本结构清晰，不需要 2048 维来捕捉细粒度语义差异
3. **存储和检索效率**：1024 vs 2048，ChromaDB 的 HNSW 向量索引体积减半，检索延迟更低
4. **官方定位**：embedding-3 文档中 1024 维定义为"高精度与效率的平衡，适合大多数应用场景"，2048 维针对"法律文档检索"等极高精度场景

如需切换维度，修改 `.env` 中的 `EMBED_DIMENSIONS` 后**必须重建知识库**：

```bash
# 例：切换到 2048 维
# .env: EMBED_DIMENSIONS=2048
python -m rag.ingest --src data/知识库 --db rag/data/chroma --force
```

---

## 费用估算

```
日均 200 次访问 × 50 token/次 × 30 天
= 300,000 token/月
= 300,000 / 1,000,000 × ¥0.5
= ¥0.15 / 月
```

知识库重建（一次性）约 5,000 token = ¥0.0025，可忽略不计。
