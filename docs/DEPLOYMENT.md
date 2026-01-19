# Deployment Guide

This guide covers deploying the Disc Golf Analyzer to Railway.

## Prerequisites

- [Railway account](https://railway.app/) (free tier available)
- [Railway CLI](https://docs.railway.app/develop/cli) (optional but recommended)
- Git repository (GitHub, GitLab, or Bitbucket)

## Architecture on Railway

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Project                       │
│                                                          │
│  ┌─────────────────┐         ┌─────────────────┐        │
│  │   api service   │         │  ml-service     │        │
│  │   (Spring Boot) │────────►│  (Flask/Python) │        │
│  │   Port 8080     │ private │  Port 5001      │        │
│  └────────┬────────┘ network └─────────────────┘        │
│           │                                              │
│           │ public                                       │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │  Public Domain  │                                    │
│  │  *.railway.app  │                                    │
│  └─────────────────┘                                    │
│                                                          │
│  ┌─────────────────┐  (optional)                        │
│  │   PostgreSQL    │                                    │
│  │   Database      │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

## Deployment Steps

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app/) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account and select this repository

### Step 3: Deploy the ML Service

1. In your Railway project, click **"New Service"**
2. Select **"GitHub Repo"** → select this repo
3. Click **"Add Root Directory"** and enter: `ml-service`
4. Railway will detect the Dockerfile and start building
5. Once deployed, note the internal URL (e.g., `ml-service.railway.internal`)

**Configure the ML Service:**
- Go to **Settings** → **Networking**
- The internal port should be `5001`
- No need for a public domain (internal only)

### Step 4: Deploy the API Service

1. Click **"New Service"** again
2. Select **"GitHub Repo"** → select this repo
3. Leave root directory as `/` (root)
4. Railway will detect the Dockerfile and start building

**Configure Environment Variables:**

Go to **Variables** tab and add:

| Variable | Value |
|----------|-------|
| `ML_SERVICE_URL` | `http://ml-service.railway.internal:5001` |
| `H2_CONSOLE_ENABLED` | `false` |
| `PORT` | `8080` |

**Configure Networking:**
- Go to **Settings** → **Networking**
- Click **"Generate Domain"** to get a public URL

### Step 5: (Optional) Add PostgreSQL

For persistent data storage:

1. Click **"New Service"** → **"Database"** → **"PostgreSQL"**
2. Railway will provision a PostgreSQL instance
3. Copy the connection variables to the API service:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `jdbc:postgresql://${PGHOST}:${PGPORT}/${PGDATABASE}` |
| `DATABASE_DRIVER` | `org.postgresql.Driver` |
| `DATABASE_USERNAME` | `${PGUSER}` |
| `DATABASE_PASSWORD` | `${PGPASSWORD}` |
| `JPA_PLATFORM` | `org.hibernate.dialect.PostgreSQLDialect` |

> Note: You'll need to add the PostgreSQL driver to `pom.xml`

### Step 6: (Optional) Enable Claude AI

To enable AI-enhanced feedback:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_ENABLED` | `true` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` (your API key) |

## Environment Variables Reference

### API Service (Spring Boot)

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |
| `ML_SERVICE_URL` | `http://localhost:5001` | ML service URL |
| `ML_SERVICE_MOCK` | `false` | Use mock responses |
| `DATABASE_URL` | H2 in-memory | Database connection URL |
| `ANTHROPIC_ENABLED` | `false` | Enable Claude AI |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `POSE_ANALYSIS_ENABLED` | `true` | Enable pose detection |

### ML Service (Flask)

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5001` | Server port |
| `FLASK_ENV` | `production` | Flask environment |

## Verifying Deployment

### Check Service Health

```bash
# API health check
curl https://your-app.railway.app/api/throws/health

# Should return: "OK"
```

### Test Video Analysis

```bash
curl -X POST \
  -F "video=@test-throw.mp4" \
  https://your-app.railway.app/api/throws/analyze-enhanced
```

## Local Development with Docker

```bash
# Build and run both services
docker-compose up --build

# API available at: http://localhost:8080
# ML service at: http://localhost:5001
```

## Costs

Railway pricing (as of 2024):
- **Free tier**: $5/month credit, enough for light testing
- **Hobby plan**: $5/month, includes more resources
- **Pro plan**: Usage-based pricing

Estimated costs for this app:
- Low traffic: ~$5-10/month
- Medium traffic: ~$15-30/month

## Troubleshooting

### ML Service Not Connecting

1. Check the ML service is running: Railway dashboard → ml-service → Deployments
2. Verify the internal URL in API service variables
3. Check logs for connection errors

### Build Failures

1. Check Railway build logs
2. Ensure Dockerfiles are valid: `docker build .`
3. MediaPipe may need specific system dependencies (included in Dockerfile)

### Memory Issues

If the ML service runs out of memory:
1. Upgrade to a larger instance
2. Reduce video processing: lower frame rate, shorter clips
3. Consider client-side processing for mobile apps

## Railway CLI Commands

```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Open dashboard
railway open

# Deploy
railway up
```
