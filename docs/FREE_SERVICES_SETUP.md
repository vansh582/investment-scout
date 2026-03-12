# Free Services Setup Guide

Complete guide to setting up all free services required for Investment Scout deployment.

## Overview

Investment Scout runs entirely on free-tier services with zero infrastructure costs:

| Service | Purpose | Free Tier | Sign Up |
|---------|---------|-----------|---------|
| **SendGrid** | Email delivery | 100 emails/day | https://sendgrid.com/free/ |
| **PostgreSQL** | Database | 500 MB - 3 GB | Multiple options below |
| **Redis** | Caching | 25-30 MB | Multiple options below |
| **Hosting** | Application | 550-1000 hours/month | Heroku, Render, Railway |
| **Cron Service** | Wake-up pings | Unlimited | https://cron-job.org/ |
| **API Keys** | Market data | Various limits | Multiple sources below |

## 1. SendGrid Email Service

**Free Tier**: 100 emails/day (more than enough for 1 newsletter + 3 alerts)

### Setup Steps

1. **Sign Up**
   - Go to https://sendgrid.com/free/
   - Click "Start for Free"
   - Fill in your details
   - Verify your email address

2. **Create API Key**
   - Log in to SendGrid dashboard
   - Go to **Settings** → **API Keys**
   - Click **"Create API Key"**
   - Name: `investment-scout`
   - Permission: **Full Access**
   - Click **"Create & View"**
   - **IMPORTANT**: Copy the API key immediately (you won't see it again)
   - Save it securely for deployment

3. **Verify Sender Email**
   - Go to **Settings** → **Sender Authentication**
   - Click **"Verify a Single Sender"**
   - Fill in your details:
     - From Name: Your name
     - From Email: Your email address
     - Reply To: Same email
     - Company Address: Your address
   - Click **"Create"**
   - Check your email and click verification link

4. **Test Email Delivery** (Optional)
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   
   message = Mail(
       from_email='your-verified-email@example.com',
       to_emails='recipient@example.com',
       subject='Test Email',
       html_content='<strong>Test successful!</strong>'
   )
   
   sg = SendGridAPIClient('YOUR_API_KEY')
   response = sg.send(message)
   print(f"Status: {response.status_code}")
   ```

### Environment Variable
```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 2. PostgreSQL Database

Choose one of these free PostgreSQL providers:

### Option A: Supabase (Recommended)

**Free Tier**: 500 MB storage, 2 GB transfer, unlimited API requests

**Pros**: 
- ✅ Generous free tier
- ✅ Automatic backups
- ✅ Built-in dashboard
- ✅ No credit card required

**Setup**:
1. Go to https://supabase.com/
2. Click "Start your project"
3. Sign in with GitHub
4. Click "New project"
5. Fill in:
   - Name: `investment-scout`
   - Database Password: (generate strong password)
   - Region: Choose closest to your hosting
6. Click "Create new project"
7. Wait for provisioning (2-3 minutes)
8. Go to **Settings** → **Database**
9. Copy **Connection string** (URI format)
10. Replace `[YOUR-PASSWORD]` with your database password

**Connection String Format**:
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

### Option B: Neon (Most Generous)

**Free Tier**: 3 GB storage, 10 GB transfer

**Pros**:
- ✅ Most generous storage
- ✅ Serverless (auto-scales to zero)
- ✅ Fast provisioning
- ✅ No credit card required

**Setup**:
1. Go to https://neon.tech/
2. Click "Sign up"
3. Sign in with GitHub
4. Click "Create a project"
5. Fill in:
   - Project name: `investment-scout`
   - Region: Choose closest to your hosting
6. Click "Create project"
7. Copy the connection string from dashboard

**Connection String Format**:
```
postgresql://user:password@ep-xxxxx.region.aws.neon.tech/neondb
```

### Option C: ElephantSQL (Easiest)

**Free Tier**: 20 MB storage (limited but sufficient for testing)

**Pros**:
- ✅ Simplest setup
- ✅ Instant provisioning
- ✅ No credit card required

**Setup**:
1. Go to https://www.elephantsql.com/
2. Click "Get a managed database today"
3. Sign up with email or GitHub
4. Click "Create New Instance"
5. Fill in:
   - Name: `investment-scout`
   - Plan: **Tiny Turtle** (Free)
   - Region: Choose closest to your hosting
6. Click "Select Region"
7. Click "Review" → "Create instance"
8. Click on your instance name
9. Copy the **URL** from instance details

**Connection String Format**:
```
postgresql://user:password@hostname.db.elephantsql.com/database
```

### Environment Variable
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
```

## 3. Redis Cache

Choose one of these free Redis providers:

### Option A: Redis Cloud (Recommended)

**Free Tier**: 30 MB storage, 30 connections

**Pros**:
- ✅ Most generous free tier
- ✅ High availability
- ✅ Good performance
- ✅ No credit card required

**Setup**:
1. Go to https://redis.com/try-free/
2. Click "Get Started"
3. Sign up with email or Google
4. Click "Create subscription"
5. Select:
   - Plan: **Free**
   - Cloud: **AWS**
   - Region: Choose closest to your hosting
6. Click "Create subscription"
7. Click "Create database"
8. Fill in:
   - Database name: `investment-scout`
   - Memory limit: 30 MB
9. Click "Activate"
10. Go to **Configuration** tab
11. Copy **Public endpoint** (format: `redis-xxxxx.c1.region.cloud.redislabs.com:port`)
12. Copy **Default user password**

**Connection String Format**:
```
redis://default:password@redis-xxxxx.c1.region.cloud.redislabs.com:12345
```

### Option B: Upstash

**Free Tier**: 10,000 commands/day, 256 MB storage

**Pros**:
- ✅ Generous command limit
- ✅ Serverless (pay per request)
- ✅ Global replication
- ✅ No credit card required

**Setup**:
1. Go to https://upstash.com/
2. Click "Get Started"
3. Sign up with email or GitHub
4. Click "Create Database"
5. Fill in:
   - Name: `investment-scout`
   - Type: **Regional**
   - Region: Choose closest to your hosting
6. Click "Create"
7. Copy **Redis Connect URL** from database details

**Connection String Format**:
```
redis://default:password@region-xxxxx.upstash.io:6379
```

### Environment Variable
```bash
REDIS_URL=redis://default:password@host:port
```

## 4. Market Data API Keys

### yfinance (Primary Source)

**Free Tier**: Unlimited (uses Yahoo Finance public data)

**Setup**: No API key required! yfinance works out of the box.

**Note**: This is your primary data source. No sign-up needed.

### Finnhub (Secondary Source)

**Free Tier**: 60 requests/minute, 30 API calls/second

**Setup**:
1. Go to https://finnhub.io/register
2. Sign up with email
3. Verify your email
4. Log in to dashboard
5. Copy your **API Key** from the dashboard

**Environment Variable**:
```bash
FINNHUB_API_KEY=your_finnhub_api_key
```

### Twelve Data (Tertiary Source)

**Free Tier**: 8 requests/minute, 800 requests/day

**Setup**:
1. Go to https://twelvedata.com/register
2. Sign up with email
3. Verify your email
4. Log in to dashboard
5. Copy your **API Key** from the dashboard

**Environment Variable**:
```bash
TWELVE_DATA_API_KEY=your_twelve_data_api_key
```

### NewsAPI (News Articles)

**Free Tier**: 100 requests/day, 1 request/second

**Setup**:
1. Go to https://newsapi.org/register
2. Sign up with email
3. Verify your email
4. Copy your **API Key** from the email or dashboard

**Environment Variable**:
```bash
NEWSAPI_KEY=your_newsapi_key
```

### FRED (Economic Data)

**Free Tier**: Unlimited requests

**Setup**:
1. Go to https://fred.stlouisfed.org/
2. Click "My Account" → "API Keys"
3. Sign up or log in
4. Click "Request API Key"
5. Fill in the form (describe your use case)
6. Submit and wait for approval email (usually instant)
7. Copy your **API Key** from the email

**Environment Variable**:
```bash
FRED_API_KEY=your_fred_api_key
```

## 5. External Cron Service

**Purpose**: Keep your app awake on free hosting platforms that sleep after inactivity

**Free Tier**: Unlimited cron jobs

### Setup cron-job.org

1. **Sign Up**
   - Go to https://cron-job.org/
   - Click "Sign up"
   - Fill in your details
   - Verify your email

2. **Create Cron Job** (After Deployment)
   - Log in to cron-job.org
   - Click "Create cronjob"
   - Fill in:
     - **Title**: Investment Scout Wake-Up
     - **URL**: `https://your-app-url.com/health`
     - **Schedule**: 
       - For Heroku: Every 25 minutes
       - For Render: Every 14 minutes
     - **Request method**: GET
     - **Enabled**: Yes
   - Click "Create cronjob"

3. **Verify**
   - Wait for first execution
   - Check "History" tab for successful pings
   - Your app should stay awake during market hours

### Alternative: UptimeRobot

**Free Tier**: 50 monitors, 5-minute intervals

1. Go to https://uptimerobot.com/
2. Sign up for free account
3. Add new monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: Investment Scout
   - URL: `https://your-app-url.com/health`
   - Monitoring Interval: 5 minutes
4. Save monitor

## 6. Complete Environment Variables

After setting up all services, you'll have these environment variables:

```bash
# Required
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RECIPIENT_EMAIL=your_email@example.com
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://default:password@host:port

# Optional (but recommended)
FINNHUB_API_KEY=your_finnhub_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key
NEWSAPI_KEY=your_newsapi_key
FRED_API_KEY=your_fred_api_key

# Configuration
NEWSLETTER_TIME=09:00
TIMEZONE=America/New_York
LOG_LEVEL=INFO
MAX_TRADING_ALERTS_PER_DAY=3
ACTIVE_STOCK_TTL=15
WATCHLIST_STOCK_TTL=60
```

## 7. Cost Monitoring

### SendGrid
- Dashboard: https://app.sendgrid.com/
- Monitor: **Email Activity** → Check daily usage
- Limit: 100 emails/day
- Alert: Set up email alerts at 80% usage

### PostgreSQL
Monitor storage usage in your provider's dashboard:
- **Supabase**: Settings → Database → Storage
- **Neon**: Dashboard → Storage usage
- **ElephantSQL**: Instance details → Database size

### Redis
Monitor memory usage in your provider's dashboard:
- **Redis Cloud**: Database → Metrics → Memory usage
- **Upstash**: Database → Metrics → Memory

### API Keys
Monitor request counts:
- **Finnhub**: Dashboard → Usage
- **Twelve Data**: Dashboard → API Calls
- **NewsAPI**: Dashboard → Usage

## 8. Security Best Practices

### Protect Your API Keys

1. **Never commit API keys to Git**
   ```bash
   # Add to .gitignore
   .env
   .env.local
   .env.production
   ```

2. **Use environment variables**
   - Store keys in hosting platform's environment variables
   - Never hardcode keys in source code

3. **Rotate keys regularly**
   - Change API keys every 90 days
   - Update in all deployment environments

4. **Limit key permissions**
   - Use minimum required permissions
   - Create separate keys for dev/prod

### Database Security

1. **Use strong passwords**
   - Minimum 16 characters
   - Mix of letters, numbers, symbols
   - Use password manager

2. **Restrict access**
   - Only allow connections from your hosting platform
   - Use SSL/TLS for connections

3. **Regular backups**
   - Enable automatic backups (Supabase, Neon)
   - Test restore process

## 9. Troubleshooting

### SendGrid Issues

**Problem**: Emails not sending
- Check API key is correct
- Verify sender email is verified
- Check SendGrid dashboard for errors
- Review daily limit (100 emails/day)

### Database Issues

**Problem**: Connection timeout
- Verify connection string is correct
- Check database is running
- Verify firewall rules allow connections
- Check SSL requirements

### Redis Issues

**Problem**: Connection refused
- Verify connection string is correct
- Check Redis is running
- Verify password is correct
- Check connection limit not exceeded

### API Rate Limits

**Problem**: Too many requests
- Implement exponential backoff
- Use caching aggressively
- Spread requests over time
- Add more free API sources

## 10. Next Steps

After setting up all services:

1. ✅ Save all API keys and connection strings securely
2. ✅ Test each service individually
3. ✅ Proceed to deployment guide
4. ✅ Configure environment variables in hosting platform
5. ✅ Deploy application
6. ✅ Set up cron job for wake-up pings
7. ✅ Monitor usage and logs

## Support

If you encounter issues:
- Check provider status pages
- Review provider documentation
- Check application logs
- Verify environment variables are set correctly
