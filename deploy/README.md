# deploy/ — 部署配置

目标环境：腾讯云轻量服务器（2C4G），Ubuntu 20.04+。架构：Nginx 反代（80/443）→ uvicorn（127.0.0.1:8000，systemd 守护）。

| 文件 | 用途 |
| --- | --- |
| [deploy.sh](deploy.sh) | 一键部署脚本：`sudo ./deploy.sh [域名]`（传域名则自动配 HTTPS） |
| [nginx.conf](nginx.conf) | SPA 静态托管 + `/api/` 反代 + 安全响应头 |
| [xiehaoyu-agent.service](xiehaoyu-agent.service) | systemd 服务（uvicorn 单 worker + `--proxy-headers` + 安全加固） |

## 一键部署步骤

`deploy.sh` 依次执行：① 安装系统依赖（Python/Nginx/certbot）→ ② 拉取代码到 `/srv/xiehaoyu-agent` → ③ 建 venv 装依赖 → ④ 配置 `.env`（不存在则从 `.env.example` 复制并提示填密钥）→ ⑤ 构建前端（`npm install && npm run build`）→ ⑥ 配置 Nginx + systemd，可选签发 SSL 证书。

## 关键配置点

- **SSE 必须禁缓冲**：`nginx.conf` 中 `proxy_buffering off` + `proxy_cache off`，后端响应头 `X-Accel-Buffering: no`，二者缺一 SSE 会变成"攒完一次性发"。
- **真实 IP**：Nginx 传 `X-Forwarded-For`，uvicorn 带 `--proxy-headers`，限流才能拿到真实客户端 IP（后端限流只信任 `request.client.host`，伪造的 XFF 第一跳无效）。
- **只读文件系统加固**：service 里 `ProtectSystem=strict`，仅 `rag/data/`、`chatbi/data/`、`data/`（会话库 sessions.db）可写。
- **依赖可复现**：部署安装 `requirements.lock`（锁定版本）而非 `requirements.txt`（宽松下限）。

## 数据初始化（首次部署必做）

以下数据文件被 `.gitignore` 排除，**不会随 `git pull` 到达服务器**，缺失时 ChatBI 必报"表不存在"、RAG 静默降级为空检索（808 审查 M6）：

1. **olist.db**（约 110MB）：将本地 `chatbi/data/olist.db` 上传到服务器同路径：
   ```bash
   scp chatbi/data/olist.db user@server:/srv/xiehaoyu-agent/chatbi/data/
   ```
   （或由 Kaggle 原始 CSV 重建：上传 `data/olist数据集/` 后 `python -m chatbi.load_olist`）
2. **Chroma 向量库**：在服务器上构建（约 1 分钟，需 `.env` 里有效的 `EMBED_API_KEY`）：
   ```bash
   cd /srv/xiehaoyu-agent && source .venv/bin/activate
   python -m rag.ingest --force
   ```
   也可上传本地已构建的 `rag/data/chroma/` 目录。
3. **sessions.db**（会话记忆）：无需准备，首次启动自动创建于 `data/sessions.db`（可用 `SESSIONS_DB_PATH` 改路径）。

验证：`curl http://127.0.0.1:8000/api/health/ready` 后，问一句"介绍一下你自己"（RAG）和"2018 年订单数"（ChatBI）各确认一次。

## 日常运维

```bash
sudo systemctl restart xiehaoyu-agent     # 重启后端
sudo journalctl -u xiehaoyu-agent -f      # 看日志
sudo nginx -t && sudo systemctl reload nginx   # 改 Nginx 配置后
```

更新代码：服务器上 `cd /srv/xiehaoyu-agent && git pull`，前端有改动则重新 `npm run build`，后端有改动则 restart 服务。
