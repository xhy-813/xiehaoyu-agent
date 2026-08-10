#!/bin/bash
# ============================================================
#  Xiehaoyu-Agent 一键部署脚本
#  适用于: Ubuntu 20.04+ / 腾讯云轻量服务器
#  用法:   chmod +x deploy.sh && sudo ./deploy.sh
# ============================================================
set -euo pipefail

APP_DIR="/srv/xiehaoyu-agent"
DOMAIN="${1:-_}"  # 可选: 传入域名, 如 ./deploy.sh agent.example.com

echo "========================================"
echo " Xiehaoyu-Agent 部署脚本"
echo "========================================"

# --- 1. System dependencies ---
echo "[1/6] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip nginx certbot python3-certbot-nginx

# --- 2. Clone / update code ---
if [ -d "$APP_DIR/.git" ]; then
    echo "[2/6] 更新代码..."
    cd "$APP_DIR"
    git pull
else
    echo "[2/6] 克隆仓库..."
    echo "请手动克隆仓库到 $APP_DIR，或修改此脚本中的仓库地址"
    echo "  git clone https://github.com/YOUR_USER/Xiehaoyu-Agent.git $APP_DIR"
    exit 1
fi

# --- 3. Python venv & dependencies ---
echo "[3/6] 安装 Python 依赖..."
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
# 使用锁定版本（requirements.lock）保证部署可复现（808 审查 M6）；
# lock 已含 fastapi/uvicorn 等全部运行依赖
pip install -q -r requirements.lock

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
    echo "  >>> 错误: 未检测到 Node.js。请先安装 Node.js (>= 18)"
    echo "  >>> 安装方法: https://nodejs.org/ 或 apt install nodejs"
    exit 1
fi
cd "$APP_DIR/frontend"

# Run npm commands as the original (non-root) user when invoked via sudo
if [ -n "${SUDO_USER:-}" ] && [ "$(id -u)" = "0" ]; then
    sudo -u "$SUDO_USER" npm install
    sudo -u "$SUDO_USER" npm run build
else
    npm install
    npm run build
fi

# --- 6. Nginx + systemd ---
echo "[6/6] 配置 Nginx 和 systemd..."

# Nginx
sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/xiehaoyu-agent
sudo ln -sf /etc/nginx/sites-available/xiehaoyu-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

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