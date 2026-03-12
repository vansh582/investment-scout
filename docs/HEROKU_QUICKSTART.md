# Heroku Quick Start Guide

Deploy Investment Scout to Heroku in under 10 minutes.

## Prerequisites

- Heroku account (sign up at https://heroku.com/)
- Git installed
- Code pushed to GitHub

## Step-by-Step Deployment

### 1. Install Heroku CLI

**macOS**:
```bash
brew tap heroku/brew && brew install heroku
```

**Windows**:
Download from https://devcenter.heroku.com/articles/heroku-cli

**Linux**:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

### 2. Login to Heroku

```bash
heroku login
```

### 3. Create Heroku App

```bash
# Clone your repository
git clone https://github.com/yourusername/investment-scout.git
cd investment-scout

# Create Heroku app
heroku create investment-scout-app

# Or use a custom name
heroku create your-custom-name
```

### 4. Add Free Database Add-ons

```bash
# Add PostgreSQL (free tier)
heroku addons:create heroku-postgresql:essential-0

# Add Redis (free tier)
heroku addons:create heroku-redis:mini

# Verify add-ons
heroku addons
```

### 5. Configure Environment Variables

**Required variables**:
```bash
heroku config:set SENDGRID_API_KEY=your_sendgrid_api_key
heroku config:set RECIPIENT_EMAIL=your_email@example.com
```

**Optional API keys** (recommended for better data coverage):
```bash
heroku config:set FINNHUB_API_KEY=your_finnhub_key
heroku config:set TWELVE_DATA_API_KEY=your_twelve_data_key
heroku config:set NEWSAPI_KEY=your_newsapi_key
heroku config:set FRED_API_KEY=your_fred_key
```

**Configuration settings**:
```bash
heroku config:set NEWSLETTER_TIME=09:00
heroku config:set TIMEZONE=America/New_York
heroku config:set LOG_LEVEL=INFO
heroku config:set MAX_TRADING_ALERTS_PER_DAY=3
heroku config:set ACTIVE_STOCK_TTL=15
heroku config:set WATCHLIST_STOCK_TTL=60
```

### 6. Deploy to Heroku

```bash
git push heroku main
```

Wait for deployment to complete (2-3 minutes).

### 7. Scale Dynos

```bash
# Start web server and worker
heroku ps:scale web=1 worker=1

# Verify dynos are running
heroku ps
```

### 8. Verify Deployment

```bash
# Check application logs
heroku logs --tail

# Open app in browser
heroku open

# Check health endpoint
curl https://your-app-name.herokuapp.com/health
```

### 9. Set Up Wake-Up Cron (Prevent Sleeping)

Heroku free tier sleeps after 30 minutes of inactivity. Prevent this:

1. Go to https://cron-job.org/ and sign up
2. Create a new cron job:
   - **Title**: Investment Scout Wake-Up
   - **URL**: `https://your-app-name.herokuapp.com/health`
   - **Schedule**: Every 25 minutes
   - **Enabled**: Yes
3. Save and activate

## Verify Everything Works

### Check Logs
```bash
heroku logs --tail
```

Look for:
- ✅ "Market Monitor started"
- ✅ "Scheduler initialized"
- ✅ "Database connected"
- ✅ "Redis connected"

### Check Database
```bash
heroku pg:info
```

### Check Redis
```bash
heroku redis:info
```

### Check Configuration
```bash
heroku config
```

## Common Issues

### Issue: "Missing required environment variable"

**Solution**: Set the missing variable
```bash
heroku config:set VARIABLE_NAME=value
```

### Issue: "Database connection failed"

**Solution**: Verify PostgreSQL add-on is provisioned
```bash
heroku addons
heroku pg:info
```

### Issue: "Redis connection failed"

**Solution**: Verify Redis add-on is provisioned
```bash
heroku addons
heroku redis:info
```

### Issue: "Email not sending"

**Solutions**:
1. Verify SendGrid API key: `heroku config:get SENDGRID_API_KEY`
2. Check SendGrid dashboard for errors
3. Verify sender email is verified in SendGrid
4. Check logs: `heroku logs --tail | grep email`

### Issue: "App is sleeping"

**Solution**: Set up cron-job.org to ping `/health` every 25 minutes (see step 9)

## Monitoring

### View Logs
```bash
# Tail logs in real-time
heroku logs --tail

# View last 1000 lines
heroku logs -n 1000

# Filter by dyno
heroku logs --dyno worker

# Search logs
heroku logs --tail | grep ERROR
```

### Check Dyno Status
```bash
heroku ps
```

### Check Resource Usage
```bash
# Database usage
heroku pg:info

# Redis usage
heroku redis:info

# Dyno hours remaining
heroku ps -a your-app-name
```

### View Metrics (in Dashboard)
1. Go to https://dashboard.heroku.com/
2. Select your app
3. Click "Metrics" tab
4. Monitor:
   - Response time
   - Memory usage
   - Throughput

## Updating Your App

### Deploy New Changes
```bash
git add .
git commit -m "Update description"
git push heroku main
```

### Restart Dynos
```bash
heroku restart
```

### Scale Dynos
```bash
# Stop worker
heroku ps:scale worker=0

# Start worker
heroku ps:scale worker=1
```

## Cost Management

### Free Tier Limits

**Dynos**: 550-1000 hours/month
- 1 web + 1 worker = 2 dynos
- 2 dynos × 24 hours × 30 days = 1440 hours needed
- **Solution**: App will sleep when inactive, wake-up cron keeps it alive during market hours

**PostgreSQL**: Essential-0 plan
- 1 GB storage
- 20 connections
- No row limit

**Redis**: Mini plan
- 25 MB storage
- 20 connections

**SendGrid**: 100 emails/day
- 1 newsletter + max 3 alerts = 4 emails/day
- Well within limit

### Monitor Usage
```bash
# Check dyno hours
heroku ps -a your-app-name

# Check database size
heroku pg:info

# Check Redis memory
heroku redis:info
```

## Useful Commands

```bash
# View environment variables
heroku config

# Set environment variable
heroku config:set KEY=value

# Unset environment variable
heroku config:unset KEY

# Run one-off command
heroku run python src/main.py

# Access database
heroku pg:psql

# Access Redis CLI
heroku redis:cli

# View add-ons
heroku addons

# Open app in browser
heroku open

# View app info
heroku info
```

## Next Steps

1. ✅ Verify health endpoint works
2. ✅ Check logs for errors
3. ✅ Set up wake-up cron job
4. ✅ Wait for first newsletter (9 AM ET)
5. ✅ Monitor SendGrid dashboard
6. ✅ Review logs daily for first week

## Support Resources

- Heroku Dev Center: https://devcenter.heroku.com/
- Heroku Status: https://status.heroku.com/
- Application logs: `heroku logs --tail`
- Heroku support: https://help.heroku.com/

## Cleanup (If Needed)

To delete the app and all resources:

```bash
# Delete app (this removes all add-ons too)
heroku apps:destroy your-app-name

# Confirm by typing app name
```

**Warning**: This permanently deletes all data!
