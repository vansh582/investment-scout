# Render Quick Start Guide

Deploy Investment Scout to Render in under 10 minutes using Infrastructure as Code.

## Prerequisites

- Render account (sign up at https://render.com/)
- GitHub account
- Code pushed to GitHub repository

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your repository contains:
- ✅ `render.yaml` (already included)
- ✅ `requirements.txt` (already included)
- ✅ Application code in `src/` directory

### 2. Sign Up for Render

1. Go to https://render.com/
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or email
4. Authorize Render to access your GitHub repositories

### 3. Create New Blueprint

1. In Render dashboard, click **"New +"** button
2. Select **"Blueprint"**
3. Connect your GitHub repository:
   - If first time: Click "Connect GitHub" and authorize
   - Select your `investment-scout` repository
4. Render will automatically detect `render.yaml`
5. Click **"Apply"**

### 4. Configure Environment Variables

Render will create services but needs environment variables. For each service (web and worker):

1. Click on the service name
2. Go to **"Environment"** tab
3. Add these variables:

**Required**:
```
SENDGRID_API_KEY = your_sendgrid_api_key
RECIPIENT_EMAIL = your_email@example.com
```

**Optional** (recommended):
```
FINNHUB_API_KEY = your_finnhub_key
TWELVE_DATA_API_KEY = your_twelve_data_key
NEWSAPI_KEY = your_newsapi_key
FRED_API_KEY = your_fred_key
```

4. Click **"Save Changes"**

**Note**: `DATABASE_URL` and `REDIS_URL` are automatically set by Render from the database services.

### 5. Monitor Deployment

1. Go to **"Events"** tab to see deployment progress
2. Wait for all services to deploy (3-5 minutes):
   - ✅ investment-scout-db (PostgreSQL)
   - ✅ investment-scout-redis (Redis)
   - ✅ investment-scout-web (Web server)
   - ✅ investment-scout-worker (Background worker)

3. Check **"Logs"** tab for any errors

### 6. Verify Deployment

1. Click on the **web service**
2. Copy the service URL (e.g., `https://investment-scout-web.onrender.com`)
3. Visit the health endpoint:
   ```
   https://your-app.onrender.com/health
   ```
4. You should see: `{"status": "healthy"}`

### 7. Set Up Wake-Up Cron (Prevent Sleeping)

Render free tier sleeps after 15 minutes of inactivity. Prevent this:

1. Go to https://cron-job.org/ and sign up
2. Create a new cron job:
   - **Title**: Investment Scout Wake-Up
   - **URL**: `https://your-app.onrender.com/health`
   - **Schedule**: Every 14 minutes
   - **Enabled**: Yes
3. Save and activate

**Why 14 minutes?** Render sleeps after 15 minutes, so pinging every 14 minutes keeps it awake.

## Verify Everything Works

### Check Service Status

1. Go to Render dashboard
2. All services should show green "Live" status:
   - 🟢 investment-scout-web
   - 🟢 investment-scout-worker
   - 🟢 investment-scout-db
   - 🟢 investment-scout-redis

### Check Logs

1. Click on **worker service**
2. Go to **"Logs"** tab
3. Look for:
   - ✅ "Market Monitor started"
   - ✅ "Scheduler initialized"
   - ✅ "Database connected"
   - ✅ "Redis connected"

### Check Database

1. Click on **investment-scout-db**
2. Go to **"Info"** tab
3. Verify:
   - Status: Available
   - Plan: Free
   - Region: Oregon

### Check Redis

1. Click on **investment-scout-redis**
2. Go to **"Info"** tab
3. Verify:
   - Status: Available
   - Plan: Free
   - Region: Oregon

## Common Issues

### Issue: "Service failed to start"

**Solution**: Check logs for specific error
1. Click on the failing service
2. Go to "Logs" tab
3. Look for error messages
4. Common causes:
   - Missing environment variables
   - Invalid database connection
   - Python dependency issues

### Issue: "Missing environment variable"

**Solution**: Add the variable
1. Click on service
2. Go to "Environment" tab
3. Add missing variable
4. Click "Save Changes"
5. Service will automatically redeploy

### Issue: "Database connection failed"

**Solution**: Verify database service
1. Check database service is "Live"
2. Verify `DATABASE_URL` is set in web/worker services
3. Check database logs for errors

### Issue: "Redis connection failed"

**Solution**: Verify Redis service
1. Check Redis service is "Live"
2. Verify `REDIS_URL` is set in web/worker services
3. Check Redis logs for errors

### Issue: "Email not sending"

**Solutions**:
1. Verify `SENDGRID_API_KEY` is set correctly
2. Check SendGrid dashboard for errors
3. Verify sender email is verified in SendGrid
4. Check worker logs for email errors

### Issue: "App is sleeping"

**Solution**: Set up cron-job.org to ping `/health` every 14 minutes (see step 7)

## Monitoring

### View Logs

1. Click on service (web or worker)
2. Go to **"Logs"** tab
3. Use search box to filter logs
4. Click "Download" to save logs

### View Metrics

1. Click on service
2. Go to **"Metrics"** tab
3. Monitor:
   - CPU usage
   - Memory usage
   - Request count (web service)
   - Response time (web service)

### View Events

1. Click on service
2. Go to **"Events"** tab
3. See deployment history and status changes

### Database Metrics

1. Click on **investment-scout-db**
2. Go to **"Metrics"** tab
3. Monitor:
   - Connection count
   - Storage usage
   - Query performance

## Updating Your App

### Automatic Deployment

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will:
1. Detect the push
2. Build new version
3. Deploy automatically
4. Show progress in "Events" tab

### Manual Deployment

1. Go to service in Render dashboard
2. Click **"Manual Deploy"** button
3. Select **"Deploy latest commit"**
4. Click **"Deploy"**

### Suspend Service

To temporarily stop a service:
1. Click on service
2. Click **"Suspend"** button
3. Confirm suspension

To resume:
1. Click **"Resume"** button

## Cost Management

### Free Tier Limits

**Web Service**: 750 hours/month
- Sleeps after 15 minutes of inactivity
- Wakes up on request (30-60 seconds)
- Use cron job to keep awake during market hours

**Worker Service**: 750 hours/month
- Sleeps after 15 minutes of inactivity
- Use cron job to keep awake

**PostgreSQL**: Free tier
- 1 GB storage
- 90 days data retention
- Automatic backups

**Redis**: Free tier
- 25 MB storage
- No persistence
- Automatic eviction (allkeys-lru)

**Bandwidth**: 100 GB/month
- More than enough for this application

### Monitor Usage

1. Go to **"Account Settings"**
2. Click **"Usage"** tab
3. Monitor:
   - Build minutes used
   - Bandwidth used
   - Active services

### Optimize Costs

To stay within free tier:
1. ✅ Use cron job to keep services awake only during market hours
2. ✅ Suspend services when not needed
3. ✅ Monitor database size (stay under 1 GB)
4. ✅ Use aggressive Redis eviction (already configured)

## Useful Features

### Environment Groups

Share environment variables across services:
1. Go to **"Environment Groups"**
2. Create new group
3. Add common variables
4. Link to services

### Custom Domains

Add your own domain (free):
1. Click on web service
2. Go to **"Settings"** tab
3. Scroll to **"Custom Domain"**
4. Add your domain
5. Update DNS records

### Notifications

Get notified of deployments:
1. Go to **"Account Settings"**
2. Click **"Notifications"**
3. Enable email or Slack notifications

### Shell Access

Access service shell:
1. Click on service
2. Click **"Shell"** tab
3. Run commands directly

## Useful Commands

### View Service URL
```bash
# Web service URL is shown in dashboard
# Format: https://service-name.onrender.com
```

### Connect to Database
```bash
# Get connection string from database service
# Use psql or any PostgreSQL client
psql "postgresql://user:pass@host/db"
```

### Connect to Redis
```bash
# Get connection string from Redis service
# Use redis-cli
redis-cli -u "redis://host:port"
```

## Next Steps

1. ✅ Verify all services are "Live"
2. ✅ Check logs for errors
3. ✅ Set up wake-up cron job
4. ✅ Test health endpoint
5. ✅ Wait for first newsletter (9 AM ET)
6. ✅ Monitor SendGrid dashboard
7. ✅ Review logs daily for first week

## Support Resources

- Render Docs: https://render.com/docs
- Render Status: https://status.render.com/
- Render Community: https://community.render.com/
- Service logs: Available in dashboard

## Cleanup (If Needed)

To delete all services:

1. Go to Render dashboard
2. Click on each service
3. Go to **"Settings"** tab
4. Scroll to bottom
5. Click **"Delete Service"**
6. Confirm deletion

**Warning**: This permanently deletes all data!

## Advantages of Render

✅ **Infrastructure as Code**: `render.yaml` defines everything
✅ **Automatic Deployments**: Push to GitHub = automatic deploy
✅ **Free SSL**: HTTPS enabled by default
✅ **Free Databases**: PostgreSQL and Redis included
✅ **Easy Scaling**: Upgrade to paid tier with one click
✅ **Great Logs**: Searchable, downloadable logs
✅ **Shell Access**: Debug directly in the service
✅ **No Credit Card**: Free tier doesn't require payment method
