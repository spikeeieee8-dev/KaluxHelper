#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  KaluxHost VPS Setup Script
#  Tested on: Ubuntu 22.04 / 24.04, Debian 12
#  Run as root or with sudo privileges.
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()    { echo -e "\n${BOLD}── $* ──────────────────────────────────────────${NC}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${CYAN}"
cat << 'EOF'
 ██╗  ██╗ █████╗ ██╗     ██╗   ██╗██╗  ██╗██╗  ██╗ ██████╗ ███████╗████████╗
 ██║ ██╔╝██╔══██╗██║     ██║   ██║╚██╗██╔╝██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
 █████╔╝ ███████║██║     ██║   ██║ ╚███╔╝ ███████║██║   ██║███████╗   ██║   
 ██╔═██╗ ██╔══██║██║     ██║   ██║ ██╔██╗ ██╔══██║██║   ██║╚════██║   ██║   
 ██║  ██╗██║  ██║███████╗╚██████╔╝██╔╝ ██╗██║  ██║╚██████╔╝███████║   ██║   
 ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   
EOF
echo -e "${NC}${BOLD}                        VPS Setup Script${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────────${NC}\n"

# ── Root check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  error "Please run this script as root: sudo bash setup-vps.sh"
fi

# ── Config ────────────────────────────────────────────────────────────────────
INSTALL_DIR="/opt/kaluxhost"
BOT_USER="kaluxhost"
API_PORT="3001"
DASHBOARD_PORT="5000"
DOMAIN=""   # Set this to your domain to auto-configure Nginx with it

# Let user override install dir
read -rp "$(echo -e "${YELLOW}Install directory [${INSTALL_DIR}]: ${NC}")" USER_DIR
[[ -n "$USER_DIR" ]] && INSTALL_DIR="$USER_DIR"

read -rp "$(echo -e "${YELLOW}Domain/IP for Nginx server_name (e.g. kaluxhost.com or your VPS IP): ${NC}")" DOMAIN
[[ -z "$DOMAIN" ]] && DOMAIN="_"   # catch-all if not set

# ── OS check ─────────────────────────────────────────────────────────────────
step "Checking OS"
if ! command -v apt-get &>/dev/null; then
  error "This script requires a Debian/Ubuntu-based system (apt-get not found)."
fi
success "Debian/Ubuntu detected"

# ── System packages ───────────────────────────────────────────────────────────
step "Installing system packages"
apt-get update -qq
apt-get install -y -qq \
  curl wget git build-essential \
  python3 python3-pip python3-venv python3-dev \
  nginx openssl ffmpeg \
  ca-certificates gnupg lsb-release
success "System packages installed"

# ── Node.js 20 ────────────────────────────────────────────────────────────────
step "Installing Node.js 20"
if ! command -v node &>/dev/null || [[ "$(node -v | cut -d. -f1 | tr -d 'v')" -lt 20 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
  success "Node.js $(node -v) installed"
else
  success "Node.js $(node -v) already present"
fi

# ── pnpm ─────────────────────────────────────────────────────────────────────
step "Installing pnpm"
if ! command -v pnpm &>/dev/null; then
  npm install -g pnpm
fi
success "pnpm $(pnpm -v) ready"

# ── Create system user ────────────────────────────────────────────────────────
step "Setting up system user: ${BOT_USER}"
if ! id "$BOT_USER" &>/dev/null; then
  useradd --system --shell /bin/bash --create-home "$BOT_USER"
  success "User ${BOT_USER} created"
else
  success "User ${BOT_USER} already exists"
fi

# ── Copy project files ────────────────────────────────────────────────────────
step "Setting up project in ${INSTALL_DIR}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

mkdir -p "$INSTALL_DIR"
rsync -a --exclude=node_modules --exclude=.git --exclude='*.pyc' \
  --exclude=__pycache__ --exclude=dist --exclude='.venv' \
  "${PROJECT_ROOT}/" "${INSTALL_DIR}/"
success "Project files copied to ${INSTALL_DIR}"

# ── Create data directory ─────────────────────────────────────────────────────
mkdir -p "${INSTALL_DIR}/data"
chown -R "$BOT_USER:$BOT_USER" "${INSTALL_DIR}"
success "Data directory ready"

# ── Generate .env file ────────────────────────────────────────────────────────
step "Creating .env file"
JWT_SECRET=$(openssl rand -hex 32)
ENV_FILE="${INSTALL_DIR}/.env"

cat > "$ENV_FILE" << EOF
# ─────────────────────────────────────────────────────────────────────────────
#  KaluxHost Environment Configuration
#  Edit this file with your values before starting services.
# ─────────────────────────────────────────────────────────────────────────────

# ── Discord Bot ───────────────────────────────────────────────────────────────
# Paste your Discord bot token below (from discord.com/developers/applications)
DISCORD_BOT_TOKEN=PASTE_YOUR_TOKEN_HERE

# ── API Server ────────────────────────────────────────────────────────────────
API_PORT=${API_PORT}

# JWT secret — auto-generated, do not change after first login
JWT_SECRET=${JWT_SECRET}

# ── Dashboard ────────────────────────────────────────────────────────────────
PORT=${DASHBOARD_PORT}
BASE_PATH=/

# ── Paths (do not change unless you moved the install directory) ──────────────
INSTALL_DIR=${INSTALL_DIR}
EOF

chmod 600 "$ENV_FILE"
chown "$BOT_USER:$BOT_USER" "$ENV_FILE"
success ".env file created at ${ENV_FILE}"

# ── Python dependencies ───────────────────────────────────────────────────────
step "Installing Python dependencies"
pip3 install -r "${INSTALL_DIR}/requirements.txt" --quiet
success "Python packages installed"

# ── Node.js dependencies ──────────────────────────────────────────────────────
step "Installing Node.js dependencies"
cd "$INSTALL_DIR"
sudo -u "$BOT_USER" pnpm install --frozen-lockfile 2>&1 | tail -5
success "Node.js packages installed"

# ── Build API Server ──────────────────────────────────────────────────────────
step "Building API server (TypeScript → JavaScript)"
cd "${INSTALL_DIR}/artifacts/api-server"
sudo -u "$BOT_USER" pnpm build 2>&1 | tail -5
success "API server compiled to dist/"

# ── Build Dashboard ───────────────────────────────────────────────────────────
step "Building dashboard (React → static files)"
cd "${INSTALL_DIR}/artifacts/dashboard"
# PORT and BASE_PATH are required by vite.config.ts even during build
PORT="${DASHBOARD_PORT}" BASE_PATH="/" sudo -u "$BOT_USER" \
  bash -c "cd ${INSTALL_DIR}/artifacts/dashboard && pnpm build" 2>&1 | tail -5
success "Dashboard built to artifacts/dashboard/dist/public/"

# ── Systemd: Discord Bot ──────────────────────────────────────────────────────
step "Creating systemd service: kaluxhost-bot"
cat > /etc/systemd/system/kaluxhost-bot.service << EOF
[Unit]
Description=KaluxHost Discord Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${BOT_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=/usr/bin/python3 bot.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kaluxhost-bot

[Install]
WantedBy=multi-user.target
EOF
success "kaluxhost-bot.service created"

# ── Systemd: API Server ───────────────────────────────────────────────────────
step "Creating systemd service: kaluxhost-api"
cat > /etc/systemd/system/kaluxhost-api.service << EOF
[Unit]
Description=KaluxHost API Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${BOT_USER}
WorkingDirectory=${INSTALL_DIR}/artifacts/api-server
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=/usr/bin/node dist/index.js
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kaluxhost-api

[Install]
WantedBy=multi-user.target
EOF
success "kaluxhost-api.service created"

# ── Nginx config ──────────────────────────────────────────────────────────────
step "Configuring Nginx"
NGINX_CONF="/etc/nginx/sites-available/kaluxhost"
DASHBOARD_DIST="${INSTALL_DIR}/artifacts/dashboard/dist/public"

cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    # ── Dashboard (static files) ────────────────────────────────────────────
    root ${DASHBOARD_DIST};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # ── API (proxy to Node.js) ──────────────────────────────────────────────
    location /api/ {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # ── Security headers ────────────────────────────────────────────────────
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ── Gzip ────────────────────────────────────────────────────────────────
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;
    gzip_min_length 1000;

    access_log /var/log/nginx/kaluxhost.access.log;
    error_log  /var/log/nginx/kaluxhost.error.log;
}
EOF

# Enable site, remove default if it exists
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/kaluxhost
rm -f /etc/nginx/sites-enabled/default
nginx -t && success "Nginx config valid"

# ── Enable & start services ───────────────────────────────────────────────────
step "Enabling services"
systemctl daemon-reload
systemctl enable kaluxhost-bot kaluxhost-api nginx
systemctl restart nginx
success "Services enabled and Nginx restarted"

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅  Setup complete!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}\n"
echo -e "${BOLD}Next steps:${NC}"
echo -e "  1. ${YELLOW}Add your Discord bot token:${NC}"
echo -e "     nano ${ENV_FILE}"
echo -e "     → Replace PASTE_YOUR_TOKEN_HERE with your actual token\n"
echo -e "  2. ${YELLOW}Start the services:${NC}"
echo -e "     systemctl start kaluxhost-bot"
echo -e "     systemctl start kaluxhost-api\n"
echo -e "  3. ${YELLOW}Check they're running:${NC}"
echo -e "     systemctl status kaluxhost-bot"
echo -e "     systemctl status kaluxhost-api\n"
echo -e "  4. ${YELLOW}View live logs:${NC}"
echo -e "     journalctl -u kaluxhost-bot -f"
echo -e "     journalctl -u kaluxhost-api -f\n"
echo -e "  5. ${YELLOW}Dashboard:${NC}  http://${DOMAIN}"
echo -e "     Default login: admin / admin123"
echo -e "     ${RED}Change your password immediately after first login!${NC}\n"
echo -e "  6. ${YELLOW}(Optional) HTTPS with Let's Encrypt:${NC}"
echo -e "     apt install certbot python3-certbot-nginx -y"
echo -e "     certbot --nginx -d your-domain.com\n"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  Install dir : ${INSTALL_DIR}"
echo -e "  .env file   : ${ENV_FILE}"
echo -e "  JWT Secret  : auto-generated ✓"
echo -e "  API Port    : ${API_PORT}"
echo -e "  Nginx       : http://${DOMAIN}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}\n"
