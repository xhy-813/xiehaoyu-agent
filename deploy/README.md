# deploy/ — 部署配置

目标环境：腾讯云轻量服务器（2C4G），Ubuntu 20.04+。架构：Nginx 反代（80/443）→ uvicorn（127.0.0.1:8000，systemd 守护）。

| 文件 | 用途 |
| --- | --- |
| [deploy.sh](deploy.sh) | 一键部署脚本：`sudo ./deploy.sh [域名]`（传域名则自动配 HTTPS） |
| [nginx.conf](nginx.conf) | SPA 静态托管 + `/api/` 反代 + 安全响应头 |
| [xiehaoyu-agent.service](xiehaoyu-agent.service) | systemd 服务（uvicorn 单 worker + `--proxy-headers` + 安全加固） |

## 一键部署步骤

`deploy.sh` 依次执行：① 安装系统依赖（git/Python/Nginx/certbot）→ ② 克隆或更新代码到 `/srv/xiehaoyu-agent`（Gitee 公开仓，脚本内 `REPO_URL`；git/npm 均以部署用户身份执行，避免 root 触发 git dubious ownership 及所有权混乱）→ ③ 建 venv 装依赖 → ④ 配置 `.env`（不存在则从 `.env.example` 复制并提示填密钥）→ ⑤ 构建前端（`npm install && npm run build`）→ ⑥ 配置 Nginx + systemd + 修正数据目录所有权，可选签发 SSL 证书。

默认走国内镜像源加速（腾讯云内网 pip 镜像 + npmmirror），可用环境变量覆盖：`PIP_INDEX_URL`、`NPM_REGISTRY`。

## 关键配置点

- **SSE 必须禁缓冲**：`nginx.conf` 中 `proxy_buffering off` + `proxy_cache off`，后端响应头 `X-Accel-Buffering: no`，二者缺一 SSE 会变成"攒完一次性发"。
- **真实 IP**：Nginx 传 `X-Forwarded-For`，uvicorn 带 `--proxy-headers`，限流才能拿到真实客户端 IP（后端限流只信任 `request.client.host`，伪造的 XFF 第一跳无效）。
- **只读文件系统加固**：service 里 `ProtectSystem=strict`，仅 `rag/data/`、`chatbi/data/`、`data/`（会话库 sessions.db）可写。
- **数据目录所有权**：服务以 `www-data` 运行，脚本会创建 `rag/data/` 并属 `www-data`（该目录被 gitignore 排除，clone 后不存在；Chroma 底层 SQLite WAL 必须可写），并把 `data/` **目录本身** chown 给 www-data（不递归——知识库文件仍属部署用户，`git pull` 更新不受影响）。`chatbi/data/` 无需写：`query_data` 以 `mode=ro` 只读连接打开 olist.db。
- **SSL 配置保护**：`certbot --nginx` 会把 443 server 块直接写进 `/etc/nginx/sites-available/xiehaoyu-agent`；脚本检测到该文件已含 `ssl_certificate` 时跳过覆盖，防止重跑 deploy.sh 丢 HTTPS。确需更新 Nginx 配置时先备份 SSL 块再手动合并。
- **依赖可复现**：部署安装 `requirements.lock`（锁定直接依赖版本，传递依赖均为小包由 pip 解析）而非 `requirements.txt`（宽松下限）。本地 BGE 兜底依赖（sentence-transformers + torch，~2.5GB）已拆到根目录 `requirements-embed-local.txt`，走智谱 API 时不装。

## 数据初始化（首次部署必做）

以下数据文件被 `.gitignore` 排除，**不会随 `git pull` 到达服务器**，缺失时 ChatBI 必报"表不存在"、RAG 静默降级为空检索（808 审查 M6）：

1. **olist.db**（约 110MB）：将本地 `chatbi/data/olist.db` 上传到服务器同路径：
   ```bash
   scp chatbi/data/olist.db user@server:/srv/xiehaoyu-agent/chatbi/data/
   ```
   （或由 Kaggle 原始 CSV 重建：上传 `data/olist数据集/` 后 `python -m chatbi.load_olist`）
2. **Chroma 向量库**：在服务器上构建（约 1 分钟，需 `.env` 里有效的 `EMBED_API_KEY`）。必须以服务用户 `www-data` 身份运行——否则生成的文件属部署用户，systemd 服务（www-data）打不开：
   ```bash
   cd /srv/xiehaoyu-agent
   sudo -u www-data .venv/bin/python -m rag.ingest --force
   ```
   也可上传本地已构建的 `rag/data/chroma/` 目录，上传后执行 `sudo chown -R www-data:www-data rag/data`。
3. **sessions.db**（会话记忆）：无需准备，首次启动自动创建于 `data/sessions.db`（可用 `SESSIONS_DB_PATH` 改路径）。

验证：`curl http://127.0.0.1:8000/api/health/ready` 后，问一句"介绍一下你自己"（RAG）和"2018 年订单数"（ChatBI）各确认一次。

## 日常运维

```bash
sudo systemctl restart xiehaoyu-agent     # 重启后端
sudo journalctl -u xiehaoyu-agent -f      # 看日志
sudo nginx -t && sudo systemctl reload nginx   # 改 Nginx 配置后
```

更新代码：服务器上 `cd /srv/xiehaoyu-agent && git pull`，前端有改动则重新 `npm run build`，后端有改动则 restart 服务。

2C4G 建议加 2GB swap（pip 安装 / npm build 内存峰值兜底）：

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

智谱 API 不可用、需切本地 BGE 兜底时（装 torch CPU 版 + sentence-transformers，约 400MB；venv 属 root，用 sudo 安装）：

```bash
cd /srv/xiehaoyu-agent
sudo .venv/bin/pip install -r requirements-embed-local.txt -i https://mirrors.cloud.tencent.com/pypi/simple
# 清空 .env 中的 EMBED_API_KEY，然后重启服务
```
