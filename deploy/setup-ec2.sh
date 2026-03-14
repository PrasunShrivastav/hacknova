#!/bin/bash
# ============================================================
# ARIA — EC2 GPU Instance Setup Script
# Run this on a fresh Ubuntu 22.04 GPU instance (g4dn.xlarge)
# ============================================================
set -e

echo "🚀 Setting up ARIA on EC2..."

# --- 1. System updates ---
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx certbot

# --- 2. Install NVIDIA drivers (for GPU instances) ---
echo "📦 Installing NVIDIA drivers..."
sudo apt install -y linux-headers-$(uname -r)
sudo apt install -y nvidia-driver-535
# Reboot may be needed after this — the script handles it below

# --- 3. Install Ollama ---
echo "📦 Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull models (this takes a few minutes)
echo "📥 Pulling LLM models..."
ollama pull gemma3:12b
ollama pull gemma3:1b

# --- 4. Clone and setup ARIA backend ---
echo "📂 Setting up ARIA backend..."
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/aria.git  # ← CHANGE THIS
cd aria/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:12b
OLLAMA_MODEL_FAST=gemma3:1b
NCBI_API_KEY=727aa387508699b0fc128e458bfa556f5208
CORS_ORIGINS=https://your-app.vercel.app
EOF

echo "⚠️  Edit /home/ubuntu/aria/backend/.env and set CORS_ORIGINS to your Vercel URL"

# --- 5. Create systemd service for ARIA backend ---
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/aria.service > /dev/null << 'EOF'
[Unit]
Description=ARIA Backend API
After=network.target ollama.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/aria/backend
Environment=PATH=/home/ubuntu/aria/backend/venv/bin:/usr/bin
ExecStart=/home/ubuntu/aria/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable aria
sudo systemctl start aria

# --- 6. Setup Nginx reverse proxy ---
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/aria > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # API requests
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;  # Long timeout for LLM responses
        proxy_buffering off;      # Important for SSE streaming
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/aria /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "============================================"
echo "  ✅ ARIA deployed successfully!"
echo "============================================"
echo ""
echo "  Backend:  http://$(curl -s ifconfig.me):80"
echo "  Ollama:   Running locally on port 11434"
echo ""
echo "  Next steps:"
echo "  1. Edit .env: set CORS_ORIGINS to your Vercel URL"
echo "  2. Deploy frontend to Vercel with:"
echo "     VITE_API_URL=http://YOUR_EC2_IP/api"
echo "  3. Restart: sudo systemctl restart aria"
echo ""
