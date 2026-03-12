# Investment Scout Deployment Guide

This guide covers deploying Investment Scout to free hosting platforms with zero infrastructure costs.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Free Service Setup](#free-service-setup)
3. [Heroku Deployment](#heroku-deployment)
4. [Render Deployment](#render-deployment)
5. [Railway Deployment](#railway-deployment)
6. [Local Development](#local-development)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Git installed
- Python 3.11+ installed locally
- GitHub account (for repository hosting)
- Email address for receiving newsletters

## Free Service Setup

Before deploying, sign up for these free services:

### 1. SendGrid (Email Delivery)

**Free Tier**: 100 emails/day

1. Sign up at https://sendgrid.com/free/
2. Verify your email address
3. Create an API key:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Choose "Full Access"
   - Copy the API key (save it securely)
4. Verify a sender email:
   - Go to Settings → Sender Authentication
   - Verify a Single Sender
   - Use the email you want to send from

### 2. PostgreSQL Database (Choose One)

#### Option A: ElephantSQL (Easiest)
**Free Tier**: 20 MB storage

1. Sign up at https://www.elephantsql.com/
2. Create a new instance:
   - Name: investment-scout
   - Plan: Tiny Turtle (Free)
   - Region: Choose closest to your hosting
3. Copy the connection URL from the instance details

#### Option B: Supabase (Recommended)
**Free Tier**: 500 MB storage, 2 GB transfer

1. Sign up at https://supabase.com/
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (URI format)
5. Replace `[YOUR-PASSWORD]` with your database password

#### Option C: Neon (Most Generous)
**Free Tier**: 3 GB storage

1. Sign up at https://neon.tech/
2. Create a new project
3. Copy the connection string from the dashboard

### 3. Redis Cache (Choose One)

#### Option A: Redis Cloud (Recommended)
**Free Tier**: 30 MB storage

1. Sign up at https://redis.com/try-free/
2. Create a new subscription:
   - Plan: Free
   - Cloud: AWS
   - Region: Choose closest to your hosting
3. Create a database
4. Copy the connection URL (format: `redis://default:password@host:port`)

#### Option B: Upstash
**Free Tier**: 10,000 commands/day

1. Sign up at https://upstash.com/
2. Create a Redis database
3. Copy the connection URL

### 4. Optional API Keys

#### Finnhub (Market Data)
**Free Tier**: 60 requests/minute

1. Sign up at https://finnhub.io/register
2. Copy your API key from the dashboard

#### Twelve Data (Technical Indicators)
**Free Tier**: 8 requests/minute

1. Sign up at https://twelvedata.com/register
2. Copy your API key from the dashboard

#### NewsAPI (News Articles)
**Free Tier**: 100 requests/day

1. Sign up at https://newsapi.org/register
2. Copy your API key

#### FRED (Economic Data)
**Free Tier**: Unlimited

1. Sign up at https://fred.stlouisfed.org/
2. Request an API key
3. Copy your API key from email

### 5. External Cron Service (Wake-Up Pings)

**Free Tier**: Unlimited

1. Sign up at https://cron-job.org/
2. After deployment, create a cron job:
   - URL: `https://your-app-url.com/health`
   - Schedule: Every 25 minutes
   - This prevents free hosting platforms from sleeping

## Heroku Deployment

**Free Tier**: 550-1000 dyno hours/month (sleeps after 30 min inactivity)

### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### Step 2: Login and Create App

```bash
heroku login
heroku create investment-scout-app
```

### Step 3: Add Free Add-ons

```bash
# PostgreSQL (Essential-0 plan - free)
heroku addons:create heroku-postgresql:essential-0

# Redis (Mini plan - free)
heroku addons:create heroku-redis:mini
```

### Step 4: Set Environment Variables

```bash
# Required
heroku config:set SENDGRID_API_KEY=your_sendgrid_api_key
heroku config:set RECIPIENT_EMAIL=your_email@example.com

# Optional API keys
heroku config:set FINNHUB_API_KEY=your_finnhub_key
heroku config:set TWELVE_DATA_API_KEY=your_twelve_data_key
heroku config:set NEWSAPI_KEY=your_newsapi_key
heroku config:set FRED_API_KEY=your_fred_key

# Configuration
heroku config:set NEWSLETTER_TIME=09:00
heroku config:set TIMEZONE=America/New_York
heroku config:set LOG_LEVEL=INFO
heroku config:set MAX_TRADING_ALERTS_PER_DAY=3
```

### Step 5: Deploy

```bash
git push heroku main
```

### Step 6: Scale Dynos

```bash
# Start web and worker processes
heroku ps:scale web=1 worker=1
```

### Step 7: View Logs

```bash
heroku logs --tail
```

### Step 8: Set Up Wake-Up Cron

1. Go to https://cron-job.org/
2. Create a new cron job:
   - Title: Investment Scout Wake-Up
   - URL: `https://investment-scout-app.herokuapp.com/health`
   - Schedule: Every 25 minutes
   - Save and enable

## Render Deployment

**Free Tier**: 750 hours/month per service (sleeps after 15 min inactivity)

### Step 1: Create Render Account

1. Sign up at https://render.com/
2. Connect your GitHub account

### Step 2: Create Blueprint

1. Push your code to GitHub
2. In Render dashboard, click "New +"
3. Select "Blueprint"
4. Connect your repository
5. Render will detect `render.yaml` automatically

### Step 3: Configure Environment Variables

In the Render dashboard, add these environment variables:

**Required**:
- `SENDGRID_API_KEY`: Your SendGrid API key
- `RECIPIENT_EMAIL`: Your email address

**Optional**:
- `FINNHUB_API_KEY`: Your Finnhub API key
- `TWELVE_DATA_API_KEY`: Your Twelve Data API key
- `NEWSAPI_KEY`: Your NewsAPI key
- `FRED_API_KEY`: Your FRED API key

### Step 4: Deploy

1. Click "Apply" to create services
2. Render will automatically:
   - Create PostgreSQL database (free tier)
   - Create Redis instance (free tier)
   - Deploy web and worker services
   - Connect all services

### Step 5: Monitor Deployment

1. Go to the "Events" tab to see deployment progress
2. Check logs in the "Logs" tab
3. Once deployed, visit your web service URL

### Step 6: Set Up Wake-Up Cron

1. Go to https://cron-job.org/
2. Create a new cron job:
   - Title: Investment Scout Wake-Up
   - URL: `https://your-app.onrender.com/health`
   - Schedule: Every 14 minutes
   - Save and enable

## Railway Deployment

**Free Tier**: $5 credit/month (no sleep, but limited hours)

### Step 1: Create Railway Account

1. Sign up at https://railway.app/
2. Connect your GitHub account

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Railway will detect `railway.toml` automatically

### Step 3: Add Database Services

1. In your project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Click "New" again
4. Select "Database" → "Add Redis"

### Step 4: Configure Environment Variables

In the Railway dashboard, add these variables to your app service:

**Required**:
- `SENDGRID_API_KEY`: Your SendGrid API key
- `RECIPIENT_EMAIL`: Your email address
- `DATABASE_URL`: Reference PostgreSQL (Railway auto-fills)
- `REDIS_URL`: Reference Redis (Railway auto-fills)

**Optional**:
- `FINNHUB_API_KEY`: Your Finnhub API key
- `TWELVE_DATA_API_KEY`: Your Twelve Data API key
- `NEWSAPI_KEY`: Your NewsAPI key
- `FRED_API_KEY`: Your FRED API key
- `NEWSLETTER_TIME`: 09:00
- `TIMEZONE`: America/New_York
- `LOG_LEVEL`: INFO

### Step 5: Deploy

Railway automatically deploys on git push. Monitor deployment in the dashboard.

### Step 6: Generate Domain

1. Go to your app service settings
2. Click "Generate Domain"
3. Copy the generated URL

## Local Development

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/investment-scout.git
cd investment-scout
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Step 5: Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Application on port 8000

### Step 6: Run Application

```bash
# Run main worker
python src/main.py

# Or run web server (in another terminal)
python src/web_server.py
```

### Step 7: Stop Services

```bash
docker-compose down
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SENDGRID_API_KEY` | SendGrid API key for email delivery | `SG.xxx...` |
| `RECIPIENT_EMAIL` | Email to receive newsletters | `you@example.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FINNHUB_API_KEY` | Finnhub API key | None |
| `TWELVE_DATA_API_KEY` | Twelve Data API key | None |
| `NEWSAPI_KEY` | NewsAPI key | None |
| `FRED_API_KEY` | FRED API key | None |
| `NEWSLETTER_TIME` | Newsletter send time (HH:MM) | `09:00` |
| `TIMEZONE` | Timezone for scheduling | `America/New_York` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_TRADING_ALERTS_PER_DAY` | Max alerts per day | `3` |
| `ACTIVE_STOCK_TTL` | Cache TTL for active stocks (seconds) | `15` |
| `WATCHLIST_STOCK_TTL` | Cache TTL for watchlist stocks (seconds) | `60` |

## Troubleshooting

### Application Won't Start

**Check logs**:
```bash
# Heroku
heroku logs --tail

# Render
# View logs in dashboard

# Railway
# View logs in dashboard

# Local
docker-compose logs -f
```

**Common issues**:
- Missing required environment variables
- Invalid database connection string
- Invalid Redis connection string
- SendGrid API key not configured

### Database Connection Errors

1. Verify `DATABASE_URL` is set correctly
2. Check database service is running
3. Verify database credentials
4. Check firewall/network settings

### Redis Connection Errors

1. Verify `REDIS_URL` is set correctly
2. Check Redis service is running
3. Verify Redis credentials
4. Check connection limits (free tiers have limits)

### Email Not Sending

1. Verify SendGrid API key is valid
2. Check SendGrid sender verification
3. Verify recipient email is correct
4. Check SendGrid dashboard for delivery status
5. Review logs for email errors

### App Sleeping on Free Tier

**Symptoms**: App doesn't respond immediately, takes 30+ seconds to wake up

**Solution**: Set up external cron job to ping `/health` endpoint every 25 minutes (Heroku) or 14 minutes (Render)

### Memory Limit Exceeded

**Symptoms**: App crashes with memory errors

**Solutions**:
1. Reduce watchlist size
2. Increase cache eviction frequency
3. Process data in smaller batches
4. Upgrade to paid tier with more memory

### Rate Limit Errors

**Symptoms**: API errors about rate limits

**Solutions**:
1. Verify API keys are correct
2. Reduce polling frequency
3. Use more aggressive caching
4. Add more free API sources for failover

### Newsletter Not Sent at Correct Time

1. Verify `NEWSLETTER_TIME` is set correctly
2. Verify `TIMEZONE` is set correctly
3. Check scheduler logs
4. Verify app is not sleeping at newsletter time

## Cost Monitoring

All services used are free tier, but monitor usage:

### SendGrid
- Dashboard: https://app.sendgrid.com/
- Limit: 100 emails/day
- Monitor: Email Activity

### Database Storage
- ElephantSQL: 20 MB limit
- Supabase: 500 MB limit
- Neon: 3 GB limit
- Monitor: Database size in provider dashboard

### Redis Storage
- Redis Cloud: 30 MB limit
- Upstash: 10,000 commands/day
- Monitor: Memory usage in provider dashboard

### Hosting Hours
- Heroku: 550-1000 hours/month
- Render: 750 hours/month per service
- Railway: $5 credit/month
- Monitor: Usage in provider dashboard

## Next Steps

After successful deployment:

1. Verify health endpoint: `https://your-app-url.com/health`
2. Check logs for any errors
3. Wait for first newsletter (9 AM Eastern Time)
4. Monitor email delivery in SendGrid dashboard
5. Review system logs daily for first week
6. Set up external cron job for wake-up pings
7. Monitor free tier usage limits

## Support

For issues or questions:
- Check logs first
- Review this troubleshooting guide
- Check provider status pages
- Review application documentation
