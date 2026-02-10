#!/bin/bash
# Gujarat Police SLM - Environment Setup Script
# Run this on a fresh Ubuntu 22.04/24.04 machine

set -euo pipefail

echo "=== Gujarat Police SLM - Environment Setup ==="
echo ""

# 1. System packages
echo "[1/7] Installing system packages..."
sudo apt-get update
sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    tesseract-ocr tesseract-ocr-hin tesseract-ocr-guj \
    libgl1-mesa-glx libglib2.0-0 \
    poppler-utils \
    postgresql-client \
    redis-tools \
    curl wget git build-essential \
    libpq-dev libffi-dev libssl-dev

# 2. Docker
echo "[2/7] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "  ✅ Docker installed (log out and back in for group changes)"
else
    echo "  ✅ Docker already installed"
fi

# 3. Docker Compose
echo "[3/7] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
echo "  ✅ Docker Compose ready"

# 4. Poetry
echo "[4/7] Installing Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  ✅ Poetry ready"

# 5. Node.js (for frontend)
echo "[5/7] Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    sudo npm install -g pnpm
fi
echo "  ✅ Node.js ready"

# 6. Project setup
echo "[6/7] Setting up project..."
cd "$(dirname "$0")/.."

# Create directories
mkdir -p data/{raw/{firs,chargesheets,rulings,panchnamas,investigation_reports},processed/{ocr,structured,cleaned},embeddings,training,sources}
mkdir -p configs logs backups models

# Copy env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ⚠️ Created .env from template - EDIT IT with your values!"
fi

# Install Python deps
poetry install
echo "  ✅ Python dependencies installed"

# 7. Save section mappings
echo "[7/7] Saving section mappings..."
poetry run python -m src.cli collect save-mappings
echo "  ✅ IPC↔BNS mappings saved"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run: make docker-up    (start database services)"
echo "  3. Run: make collect-acts  (download bare acts + mappings)"
echo "  4. Run: make collect-kanoon (start collecting court rulings)"
echo "  5. Place local documents in data/raw/"
echo ""
