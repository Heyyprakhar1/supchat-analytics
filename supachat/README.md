# SupaChat — Conversational Analytics Platform

[![CI/CD](https://github.com/yourusername/supachat/actions/workflows/deploy.yml/badge.svg)](https://github.com/yourusername/supachat/actions)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org/)

> **Natural language → SQL → Insights.**  
> A full-stack conversational analytics app powered by Supabase PostgreSQL, MCP servers, and modern DevOps practices.

![Architecture](https://i.imgur.com/architecture-diagram.png)

## 📑 Table of Contents
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Local Development](#-local-development)
- [Production Deployment](#-production-deployment)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Monitoring](#-monitoring)
- [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/supachat.git
cd supachat

# 2. Setup environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Run with Docker Compose
docker-compose -f infra/docker/docker-compose.yml up --build

# 4. Open http://localhost

Demo Queries:

"Show top trending topics in last 30 days"
"Compare article engagement by topic"
"Plot daily views trend for AI articles"
🏗️ Architecture
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │──────│    Nginx    │──────│   FastAPI   │──────│  Supabase   │
│  (Port 3000)│      │  (Port 80)  │      │  (Port 8000)│      │  PostgreSQL │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Grafana/Loki      │
                    │   (Port 3001)       │
                    └─────────────────────┘
Tech Stack:

Frontend: Next.js 14, React Server Components, TailwindCSS, Recharts
Backend: FastAPI, asyncpg, MCP (Model Context Protocol)
Database: Supabase PostgreSQL (managed)
DevOps: Docker, GitHub Actions, Terraform, Prometheus, Grafana
Cloud: AWS EC2, Nginx reverse proxy
📋 Prerequisites
Tool	Version	Purpose
Docker	24.0+	Containerization
Docker Compose	2.20+	Orchestration
Node.js	18.x	Frontend runtime
Python	3.11+	Backend runtime
Terraform	1.5+	Infrastructure (optional)
Supabase Account	Free tier OK	Database hosting
💻 Local Development
Backend (FastAPI)
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/api/health
Frontend (Next.js)
cd apps/web

# Install dependencies
npm install

# Run dev server
npm run dev

# Access at http://localhost:3000
Database Setup
-- Run in Supabase SQL Editor
-- Schema + sample data included in infra/db/init.sql

CREATE TABLE articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert sample data for testing
INSERT INTO articles (title, topic, views, likes) 
VALUES ('AI Revolution', 'AI', 15000, 450);
🚀 Production Deployment
Option A: Automated (Recommended)
Fork this repo

Add GitHub Secrets (Settings → Secrets → Actions):

EC2_HOST: Your EC2 public IP
EC2_USER: ec2-user (or ubuntu)
EC2_SSH_KEY: Private key content
DATABASE_URL: Supabase connection string
Push to main — GitHub Actions handles the rest:

git add .
git commit -m "Ready for production"
git push origin main
Option B: Manual (EC2)
# SSH into EC2
ssh -i key.pem ec2-user@<your-ip>

# Install Docker
sudo yum update -y
sudo yum install -y docker git
sudo service docker start
sudo usermod -a -G docker $USER

# Clone & deploy
git clone https://github.com/yourusername/supachat.git
cd supachat
cp .env.example .env
# Edit .env with production values

# Deploy
sudo docker-compose -f infra/docker/docker-compose.yml up -d
Option C: Terraform (Infrastructure as Code)
cd terraform

# Initialize
terraform init

# Plan
terraform plan -var="key_name=your-ec2-key"

# Apply
terraform apply

# Output will show the public IP
🔐 Environment Variables
Create .env file (never commit this!):

# === Database ===
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres?sslmode=require

# === Backend ===
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-postgres

# === Frontend ===
NEXT_PUBLIC_API_URL=http://localhost:8000

# === Monitoring ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=change_me_in_production

# === Optional: DevOps Agent ===
OPENAI_API_KEY=sk-...
Security Note: In production, use GitHub Secrets for CI/CD and AWS Parameter Store/Secrets Manager for EC2.

📡 API Documentation
Health Check
GET /api/health
Response:

{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
Natural Language Query
POST /api/query
Content-Type: application/json

{
  "question": "Show top trending topics in last 30 days",
  "session_id": "optional-session-id"
}
Response:

{
  "sql": "SELECT topic, SUM(views) as total_views FROM articles...",
  "data": [
    {"topic": "AI", "total_views": 45000},
    {"topic": "DevOps", "total_views": 23000}
  ],
  "chart_type": "bar",
  "explanation": "Top trending topics by views in last 30 days",
  "timestamp": "2024-01-15T10:30:00Z"
}
Interactive Docs
Visit /docs when running locally for Swagger UI.

📊 Monitoring
Once deployed, access the observability stack:

Service	URL	Credentials
SupaChat App	http://<your-ip>	Public
Grafana	http://<your-ip>:3001	admin / [from .env]
Health	http://<your-ip>/api/health	Public
Key Dashboards
API Performance: Request latency, error rates, throughput
Container Metrics: CPU, memory, restart counts
Database: Connection pool, query performance
Logs: Centralized logging with Loki
🛠️ Troubleshooting
Container won't start?
# Check logs
docker-compose logs -f api

# Check specific container
docker logs supachat-api --tail 100
Database connection refused?
Verify DATABASE_URL includes ?sslmode=require
Check Supabase Network Settings → Allow all IPs (or your EC2 IP)
Test connectivity:
docker run --rm -it postgres:15-alpine psql "$DATABASE_URL" -c "SELECT 1"
Frontend can't reach backend?
# Check if containers are on same network
docker network inspect supachat-network

# Test from frontend container
docker exec -it supachat-web wget -qO- http://api:8000/api/health
MCP Server errors?
The MCP server requires Node.js in the API container. Ensure your Dockerfile.api includes:

RUN apt-get install -y nodejs npm
RUN npm install -g @modelcontextprotocol/server-postgres
🧠 AI Tools Used
This project was built with AI assistance:

Cursor — Code generation and refactoring
Claude — Architecture design and DevOps scripts
GitHub Copilot — Boilerplate completion
ChatGPT — Documentation and debugging
🤝 Contributing
Fork the repository
Create feature branch (git checkout -b feature/amazing-feature)
Commit changes (git commit -m 'Add amazing feature')
Push to branch (git push origin feature/amazing-feature)
Open Pull Request
📄 License
MIT License — see LICENSE [blocked] for details.

Need help? Open an issue or reach out: srivprak0106@gmail.com

Built with ❤️ and ☕ by the SupaChat team.


## 📝 Key Features of this README:

1. **Visual hierarchy** — Clear sections with emojis for scannability
2. **Copy-paste ready** — All commands tested and ready to run
3. **Three deployment options** — From quick local to full Terraform
4. **Troubleshooting section** — Solves the 3 most common Docker issues
5. **API examples** — Real JSON responses they can test immediately
6. **Architecture diagram** — ASCII art shows the flow clearly

**Pro tip:** Add real screenshots of your Grafana dashboards and the chat UI once you have it run
