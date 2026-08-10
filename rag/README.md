# rag/ — RAG 个人知识库

"介绍本人"能力的检索层：把个人知识库 markdown 切片、嵌入、存入 ChromaDB，供 [agent/tools/introduce_me.py](../agent/tools/introduce_me.py) 检索。

## 数据流

```
data/知识库/**/*.md
   │  rag/ingest.py：按 H1/H2/H3 切片 → 800 字硬切（重叠 80）→ Embedding
   ▼
rag/data/chroma/（ChromaDB 持久化，collection = xhy_kb，cosine 距离）
   │  rag/retriever.py：retrieve(question, top_k)
   ▼
introduce_me 工具：检索片段 + persona prompt → LLM 生成第一人称回答
```

## 模块

| 文件 | 职责 |
| --- | --- |
| [constants.py](constants.py) | 共享常量 + `get_embedding_function()` 双模式工厂 |
| [ingest.py](ingest.py) | 语料扫描、切片、向量入库（CLI：`python -m rag.ingest`） |
| [retriever.py](retriever.py) | top-k 检索封装（`retrieve` / `count` / `invalidate_cache`） |
| `data/chroma/` | ChromaDB 持久化目录 |

## 语料与切片

- 扫描 `data/知识库/` 下 5 个顶层目录：`简历` `自我介绍` `常见问题` `项目` `工作经历`（`INCLUDE_DIRS`）。
- 显式排除 `secrets/`、`.git/` 等目录（`EXCLUDE_DIRS`）。
- 按 Markdown H1/H2/H3 标题切片，标题路径作为 breadcrumb 写入片段头（如 `# 项目 > Xiehaoyu-Agent`）；首段标题前的正文也保留。
- 单段超过 800 字时硬切，重叠 80 字，优先在句读边界（。！？.!?）下刀。
- chunk id = `文件路径::序号::md5`，幂等可重建。
- **入库前 PII 脱敏**（`_mask_pii()`）：手机号打码为前 3 后 2（`187****95`）、邮箱本地部分只留首字符（`x***@163.com`），embedding 与存储同源——公网 RAG 检索不会泄出原始联系方式。**例外**：`PII_EXEMPT` 白名单（当前仅 `常见问题/13-联系方式.md`）跳过打码——08-09 方案 T2 联系方式口径放开后，该文件专为公开联系方式而建，需保留完整邮箱/微信才能被检索引用；白名单按知识库相对路径精确匹配，其余文件维持脱敏不变。
- 入库采用**原子替换**：先写入临时 collection，全量完成后删旧换新，重建期间检索不中断。

## Embedding 双模式

`get_embedding_function()`（[constants.py](constants.py)）按环境变量自动切换：

| 模式 | 条件 | 模型 | 特点 |
| --- | --- | --- | --- |
| API 模式 | 设置了 `EMBED_API_KEY` | 智谱 `embedding-3`（默认 1024 维） | 零本地内存，2C4G 服务器友好 |
| 本地模式 | 未设置（降级兜底） | `BAAI/bge-large-zh-v1.5`（sentence-transformers） | 约 1.3GB 内存，首次需下载模型 |

**切换维度（`EMBED_DIMENSIONS`）或模型后必须重建知识库**（向量维度不兼容）：

```bash
python -m rag.ingest --force    # 跳过确认直接重建
```

本地模式下 retriever 会设置 `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`，避免每次启动访问 HuggingFace。

## 检索 API

```python
from rag.retriever import retrieve, retrieve_result, count, invalidate_cache

hits = retrieve("你 K12 项目做了什么", top_k=5)   # introduce_me 默认 top_k=10
for h in hits:
    print(h.source, h.heading, h.similarity)    # similarity = 1 - cosine distance

res = retrieve_result("...", top_k=5)   # RetrievalResult(hits, degraded)
res.degraded   # True = 检索基础设施故障（区别于"无匹配"的空结果）
```

- 默认相似度阈值 `min_similarity=0.3`，低于阈值的片段被过滤并记日志。
- collection 句柄用 `lru_cache` 缓存；重新入库后调 `invalidate_cache()` 失效缓存。
- 知识库为空/不可用时不抛异常：`retrieve()` 返回空列表；`retrieve_result()` 额外给出 `degraded` 标志，`introduce_me` 据此指示 LLM 诚实说明"知识库暂不可用"而不是凭人设编造。

## 测试

```bash
python -m tests.smoke_introduce_me   # RAG 工具冒烟（需真实 API Key）
pytest tests/test_rag.py -v          # 检索质量测试
```
