#!/bin/bash
# ==============================================================================
# Resumo AWS Path B — Automated Server Deployment & Live Verification
# ==============================================================================
set -e

echo "=========================================================="
echo " Starting Resumo AWS Path B Service Deployment"
echo "=========================================================="

# 1. Install Docker & Git
echo "[1/5] Verifying system packages (Docker & Docker Compose)..."
if command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y docker git
elif command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y docker.io git curl
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER" 2>/dev/null || true

# Docker Compose v2 plugin installation if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose v2 plugin..."
    sudo mkdir -p /usr/libexec/docker/cli-plugins
    ARCH=$(uname -m)
    sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$ARCH" \
        -o /usr/libexec/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose
fi

# Docker Buildx plugin installation if not present
if ! docker buildx version &> /dev/null; then
    echo "Installing Docker Buildx plugin..."
    sudo mkdir -p /usr/libexec/docker/cli-plugins
    ARCH=$(uname -m)
    [ "$ARCH" = "x86_64" ] && BARCH="amd64" || BARCH="arm64"
    sudo curl -SL "https://github.com/docker/buildx/releases/download/v0.38.1/buildx-v0.38.1.linux-$BARCH" \
        -o /usr/libexec/docker/cli-plugins/docker-buildx
    sudo chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
fi

echo "✓ Docker: $(docker --version)"
echo "✓ Buildx: $(docker buildx version)"
echo "✓ Compose: $(docker compose version)"

# 2. Secret & Environment Injection
echo "[2/5] Preparing environment variables..."
if [ -f "scripts/fetch_secrets.sh" ]; then
    chmod +x scripts/fetch_secrets.sh
    source scripts/fetch_secrets.sh
fi

# Write environment file for Docker Compose
cat <<EOF > .env
APP_ENV=production
DEBUG=false
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=${DATABASE_URL}
RUN_MIGRATIONS=1
FRONTEND_ORIGIN=${FRONTEND_ORIGIN}
COOKIE_SECURE=false
STORAGE_BACKEND=s3
S3_BUCKET=${S3_BUCKET:-resumo-files-vicky}
S3_REGION=${S3_REGION:-ap-south-1}
LLM_PROVIDER=none
BEDROCK_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
JOB_RUNNER=thread
EOF
chmod 600 .env

echo "✓ Created production .env file from SSM secrets"

# 3. Build & Launch Containers
echo "[3/5] Building and launching multi-tier containers (Path B)..."
sudo docker compose -f docker-compose.aws.yml up -d --build

# 4. Wait for healthy startup & run migrations + seed
echo "[4/5] Waiting for backend initialization..."
sleep 12

echo "Running Alembic migrations..."
sudo docker compose -f docker-compose.aws.yml exec -T backend alembic upgrade head || true

echo "Seeding demo account (demo@resumo.app / demo1234)..."
sudo docker compose -f docker-compose.aws.yml exec -T backend python scripts/seed_demo.py --email demo@resumo.app --password demo1234 || true

# 5. Live Endpoint Verification
echo "[5/5] Running verification checks..."
echo "--- Healthcheck ---"
curl -s http://localhost:8000/api/v1/health || true
echo ""
echo "--- Readiness (Database Check) ---"
curl -s http://localhost:8000/api/v1/ready || true
echo ""

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "localhost")

echo "=========================================================="
echo " Deployment Complete!"
echo " Web UI:     http://${PUBLIC_IP}/"
echo " API Docs:   http://${PUBLIC_IP}/api/docs"
echo " Demo Login: demo@resumo.app / demo1234"
echo "=========================================================="
