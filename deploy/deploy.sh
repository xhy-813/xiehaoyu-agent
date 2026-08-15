#!/bin/bash
# ============================================================
#  Xiehaoyu-Agent 一键部署脚本
#  适用于: Ubuntu 20.04+ / 腾讯云轻量服务器
#  用法:   chmod +x deploy.sh && sudo ./deploy.sh
# ============================================================
set -euo pipefail

APP_DIR="/srv/xiehaoyu-agent"
DOMAIN="${1:-_}"  # 可选: 传入域名, 如 ./deploy.sh agent.example.com
REPO_URL="https://gitee.com/xiehaoyu12138/xiehaoyu-agent.git"

# 仓库属主（git/npm 都以该用户执行，保证所有权一致；直接以 root 运行时为 root）
APP_USER="${SUDO_USER:-root}"

# 国内镜像源加速（腾讯云内网 pip 镜像免流量；可用环境变量覆盖）
PIP_INDEX_URL="${PIP_INDEX_URL:-https://mirrors.cloud.tencent.com/pypi/simple}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmmirror.com}"

echo "========================================"
echo " Xiehaoyu-Agent 部署脚本"
echo "========================================"

# --- 1. System dependencies ---
echo "[1/6] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx

# --- 2. Clone / update code ---
if [ -d "$APP_DIR/.git" ]; then
    echo "[2/6] 更新代码..."
    cd "$APP_DIR"
    # 以属主身份执行：root 直接 git 会被 git>=2.35 以 dubious ownership 拒绝，
    # 且 root 写出的新文件会导致后续 sudo -u npm build 权限不足
    sudo -u "$APP_USER" git pull
else
    echo "[2/6] 克隆仓库（Gitee 公开仓）..."
    git clone "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

# --- 3. Python venv & dependencies ---
echo "[3/6] 安装 Python 依赖..."
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
# 使用锁定版本（requirements.lock）保证部署可复现（808 审查 M6）；
# lock 已含 fastapi/uvicorn 等全部运行依赖。
# 本地 BGE 兜底依赖（torch 等）不在其中，需要时手动装 requirements-embed-local.txt
pip install -q -r requirements.lock -i "$PIP_INDEX_URL"

# --- 4. Environment config ---
echo "[4/6] 配置环境变量..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    # 808 审查 M8：.env 含 API 密钥，收紧权限（服务以 www-data 运行需可读）
    chown root:www-data "$APP_DIR/.env"
    chmod 640 "$APP_DIR/.env"
    echo "  >>> 请编辑 $APP_DIR/.env 填入真实密钥后重新运行此脚本"
    echo "  >>> 需要配置: DEEPSEEK_API_KEY"
    exit 1
fi
echo "  .env 已存在，跳过"
# 已有 .env 同样确保权限收紧
chown root:www-data "$APP_DIR/.env"
chmod 640 "$APP_DIR/.env"

# --- 5. Build frontend ---
echo "[5/6] 构建前端..."
if ! command -v node &> /dev/null; then
    echo "  >>> 错误: 未检测到 Node.js。请先安装 Node.js (>= 20.19，vite 8 引擎要求)"
    echo "  >>> 安装方法: https://nodejs.org/ 或 apt install nodejs"
    exit 1
fi
cd "$APP_DIR/frontend"

# Run npm commands as the original (non-root) user when invoked via sudo
if [ -n "${SUDO_USER:-}" ] && [ "$(id -u)" = "0" ]; then
    sudo -u "$SUDO_USER" npm install --registry="$NPM_REGISTRY"
    sudo -u "$SUDO_USER" npm run build
else
    npm install --registry="$NPM_REGISTRY"
    npm run build
fi

# --- 6. Nginx + systemd ---
echo "[6/6] 配置 Nginx 和 systemd..."

# Nginx —— 已有 SSL 配置时不覆盖：certbot --nginx 会把 443 server 块直接写进
# 这份文件，cp 覆盖会丢 HTTPS；确需应用 deploy/nginx.conf 的改动时，先备份该
# 文件中的 SSL 块再手动合并
NGINX_CONF="/etc/nginx/sites-available/xiehaoyu-agent"
if [ -f "$NGINX_CONF" ] && grep -q "ssl_certificate" "$NGINX_CONF"; then
    echo "  检测到已有 SSL 配置，保留现有 Nginx 配置（如需更新请手动合并 deploy/nginx.conf）"
else
    sudo cp "$APP_DIR/deploy/nginx.conf" "$NGINX_CONF"
fi
sudo ln -sf /etc/nginx/sites-available/xiehaoyu-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 数据目录所有权（systemd 加固的配套，必须在启动服务前完成）：
# 服务以 www-data 运行且 ProtectSystem=strict，以下目录必须对 www-data 可写——
#   rag/data/  Chroma 向量库（SQLite WAL）；被 gitignore 排除，clone 后不存在，需创建
#   data/      sessions.db 会话库（WAL 模式）；只改目录本身、不递归，
#              知识库文件仍属 $APP_USER，git pull 更新不受影响
# chatbi/data/ 无需处理：query_data 以 mode=ro 只读连接打开 olist.db
install -d -o www-data -g www-data "$APP_DIR/rag/data"
chown www-data:www-data "$APP_DIR/data"

# systemd
sudo cp "$APP_DIR/deploy/xiehaoyu-agent.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xiehaoyu-agent
sudo systemctl restart xiehaoyu-agent

# --- HTTPS (optional) ---
if [ "$DOMAIN" != "_" ]; then
    echo "[HTTPS] 获取 SSL 证书..."
    if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"; then
        echo "  SSL 证书获取成功！"
    else
        echo "  ⚠️  SSL 证书获取失败（exit code: $?）。"
        echo "  ⚠️  请检查 DNS 是否正确解析到本服务器，或手动运行："
        echo "  ⚠️    sudo certbot --nginx -d $DOMAIN"
    fi
fi

echo "========================================"
echo " 部署完成!"
echo " 后端: systemctl status xiehaoyu-agent"
echo " 前端: http://$(hostname -I | awk '{print $1}')"
echo " 日志: journalctl -u xiehaoyu-agent -f"
echo "========================================"