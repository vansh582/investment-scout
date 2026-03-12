# Investment Scout Deployment Checklist

Quick checklist for deploying Investment Scout to free hosting platforms.

## Pre-Deployment Setup

### 1. Free Services Sign-Up

- [ ] **SendGrid** (Email)
  - Sign up: https://sendgrid.com/free/
  - Create API key
  - Verify sender email
  - Save API key: `SENDGRID_API_KEY`

- [ ] **PostgreSQL** (Choose one)
  - [ ] Supabase: https://supabase.com/ (500 MB - Recommended)
  - [ ] Neon: https://neon.tech/ (3 GB - Most generous)
  - [ ] ElephantSQL: https://elephantsql.com/ (20 MB - Easiest)
  - Save connection URL: `DATABASE_URL`

- [ ] **Redis** (Choose one)
  - [ ] Redis Cloud: https://redis.com/try-free/ (30 MB - Recommended)
  - [ ] Upstash: https://upstash.com/ (10K commands/day)
  - Save connection URL: `REDIS_URL`

### 2. Optional API Keys (Recommended)

- [ ] **Finnhub**: https://finnhub.io/register
  - Save API key: `FINNHUB_API_KEY`

- [ ] **Twelve Data**: https://twelvedata.com/register
  - Save API key: `TWELVE_DATA_API_KEY`

- [ ] **NewsAPI**: https://newsapi.org/register
  - Save API key: `NEWSAPI_KEY`

- [ ] **FRED**: https://fred.stlouisfed.org/
  - Save API key: `FRED_API_KEY`

### 3. Code Preparation

- [ ] Push code to GitHub
- [ ] Verify all files are committed
- [ ] Check `.gitignore` excludes `.env` files

## Deployment (Choose One Platform)

### Option A: Heroku

- [ ] Install Heroku CLI
- [ ] Login: `heroku login`
- [ ] Create app: `heroku create your-app-name`
- [ ] Add PostgreSQL: `heroku addons:create heroku-postgresql:essential-0`
- [ ] Add Redis: `heroku addons:create heroku-redis:mini`
- [ ] Set environment variables (see below)
- [ ] Deploy: `git push heroku main`
- [ ] Scale dynos: `heroku ps:scale web=1 worker=1`
- [ ] Check logs: `heroku logs --tail`

### Option B: Render (Recommended)

- [ ] Sign up at https://render.com/
- [ ] Connect GitHub account
- [ ] Create new Blueprint
- [ ] Select your repository
- [ ] Render detects `render.yaml` automatically
- [ ] Add environment variables in dashboard
- [ ] Click "Apply" to deploy
- [ ] Monitor deployment in Events tab
- [ ] Check logs in Logs tab

### Option C: Railway

- [ ] Sign up at https://railway.app/
- [ ] Connect GitHub account
- [ ] Create new project from GitHub repo
- [ ] Add PostgreSQL database
- [ ] Add Redis database
- [ ] Set environment variables
- [ ] Railway auto-deploys
- [ ] Generate domain for web service

## Environment Variables

### Required (All Platforms)

```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RECIPIENT_EMAIL=your_email@example.com
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://default:password@host:port
```

### Optional (Recommended)

```bash
FINNHUB_API_KEY=your_finnhub_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key
NEWSAPI_KEY=your_newsapi_key
FRED_API_KEY=your_fred_api_key
```

### Configuration (Optional)

```bash
NEWSLETTER_TIME=09:00
TIMEZONE=America/New_York
LOG_LEVEL=INFO
MAX_TRADING_ALERTS_PER_DAY=3
ACTIVE_STOCK_TTL=15
WATCHLIST_STOCK_TTL=60
```

## Post-Deployment

### 1. Verify Deployment

- [ ] Check health endpoint: `https://your-app-url.com/health`
- [ ] Should return: `{"status": "healthy", "scheduler_running": true}`
- [ ] Review logs for errors
- [ ] Verify all services are running

### 2. Set Up Wake-Up Cron

- [ ] Sign up at https://cron-job.org/
- [ ] Create new cron job:
  - **URL**: `https://your-app-url.com/health`
  - **Schedule**: 
    - Heroku: Every 25 minutes
    - Render: Every 14 minutes
    - Railway: Not needed (no sleep)
  - **Method**: GET
  - **Enabled**: Yes
- [ ] Verify cron job executes successfully

### 3. Monitor First Day

- [ ] Check logs every few hours
- [ ] Verify no errors in logs
- [ ] Check database connections
- [ ] Check Redis connections
- [ ] Monitor memory usage

### 4. Wait for First Newsletter

- [ ] Newsletter scheduled for 9:00 AM Eastern Time
- [ ] Check email inbox
- [ ] Verify newsletter received
- [ ] Check SendGrid dashboard for delivery status
- [ ] Review newsletter content

### 5. Monitor Usage

- [ ] **SendGrid**: Check email count (limit: 100/day)
- [ ] **Database**: Check storage usage
- [ ] **Redis**: Check memory usage
- [ ] **Hosting**: Check hours used
- [ ] **APIs**: Check request counts

## Troubleshooting

### App Won't Start

1. Check logs for specific error
2. Verify all required environment variables are set
3. Check database connection string
4. Check Redis connection string
5. Review deployment guide: `docs/DEPLOYMENT_GUIDE.md`

### Database Connection Failed

1. Verify `DATABASE_URL` is correct
2. Check database service is running
3. Test connection from local machine
4. Check firewall rules

### Redis Connection Failed

1. Verify `REDIS_URL` is correct
2. Check Redis service is running
3. Verify password is correct
4. Check connection limit

### Email Not Sending

1. Verify `SENDGRID_API_KEY` is correct
2. Check sender email is verified in SendGrid
3. Check SendGrid dashboard for errors
4. Review email service logs

### App Sleeping

1. Verify cron job is set up
2. Check cron job execution history
3. Verify cron job URL is correct
4. Check cron job schedule (25 min for Heroku, 14 min for Render)

## Documentation Reference

- **Comprehensive Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Heroku Quick Start**: `docs/HEROKU_QUICKSTART.md`
- **Render Quick Start**: `docs/RENDER_QUICKSTART.md`
- **Free Services Setup**: `docs/FREE_SERVICES_SETUP.md`
- **Task Summary**: `docs/TASK_26_DEPLOYMENT_SUMMARY.md`

## Support

If you encounter issues:

1. Check the troubleshooting section in deployment guides
2. Review application logs
3. Check provider status pages
4. Verify all environment variables
5. Test services individually

## Success Criteria

✅ Health endpoint returns 200 OK
✅ Logs show no errors
✅ Database connected
✅ Redis connected
✅ Cron job pinging successfully
✅ First newsletter received at 9 AM ET
✅ All services within free tier limits

## Next Steps After Deployment

1. Monitor logs daily for first week
2. Review newsletter quality
3. Check performance metrics
4. Monitor free tier usage
5. Adjust configuration as needed
6. Set up alerts for errors
7. Document any issues encountered

---

**Estimated Time**: 30-45 minutes for complete deployment

**Cost**: $0 (all free tier services)

**Maintenance**: Monitor usage weekly, review logs daily initially
