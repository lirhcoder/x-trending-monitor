# X/Twitter Trending Monitor Setup Guide

## Overview

This guide walks you through setting up the X/Twitter Trending Monitor from scratch.

## Step 1: Get Twitter/X API Access

You have two options:

### Option A: Official Twitter API (Recommended for reliability)

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Sign up for a developer account
3. Create a new project and app
4. Generate a Bearer Token
5. Note: Free tier allows 1,500 tweets/month; Basic ($100/mo) allows 10,000

**Pros:** Official, reliable, well-documented
**Cons:** Expensive for high-volume, rate limits

### Option B: RapidAPI Alternatives (Budget-friendly)

1. Go to [rapidapi.com](https://rapidapi.com)
2. Search for "Twitter API" and choose one:
   - `twitter-api45` - Good balance of price/features
   - `twitter154` - Cheaper option
   - `twttrapi` - Another alternative
3. Subscribe to a plan (many have free tiers)
4. Get your RapidAPI key

**Pros:** Cheaper, often more generous limits
**Cons:** Third-party, may be less stable

## Step 2: Set Up Email Notifications

Choose one:

### Option A: Gmail SMTP (Simplest)

1. Enable 2FA on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate an app password for "Mail"
4. Use these settings:
   - SMTP_HOST: smtp.gmail.com
   - SMTP_PORT: 587
   - SMTP_USER: your-email@gmail.com
   - SMTP_PASSWORD: (the app password you generated)

### Option B: SendGrid (Recommended for production)

1. Sign up at [sendgrid.com](https://sendgrid.com) (free tier: 100 emails/day)
2. Verify your sender email
3. Generate an API key
4. Set:
   - SENDGRID_API_KEY: your-api-key
   - SENDGRID_FROM_EMAIL: your-verified@email.com

### Option C: AWS SES (If using AWS Lambda)

1. Set up AWS SES in your AWS console
2. Verify your sender email/domain
3. Set:
   - SES_FROM_EMAIL: your-verified@email.com
   - AWS credentials via IAM role or environment

## Step 3: Configuration

Create a `config.json` file:

```json
{
  "keywords": [
    "AI agent",
    "data visualization",
    "business intelligence",
    "数据分析",
    "ChatGPT"
  ],
  "followed_accounts": [
    "elikiyan",
    "sama",
    "karpathy"
  ],
  "rapid_growth_threshold": 1000,
  "absolute_threshold": 5000,
  "check_interval_minutes": 15
}
```

### Configuration Options

| Field | Description | Default |
|-------|-------------|---------|
| `keywords` | List of search terms to monitor | Required |
| `followed_accounts` | Twitter usernames to monitor | Required |
| `rapid_growth_threshold` | Engagement/hour to trigger alert | 1000 |
| `absolute_threshold` | Total engagement to trigger alert | 5000 |
| `check_interval_minutes` | How often to check (for scheduled runs) | 15 |

## Step 4: Environment Variables

Set these environment variables:

```bash
# Twitter API (choose one)
TWITTER_BEARER_TOKEN=your-token-here
# OR
RAPIDAPI_KEY=your-rapidapi-key
RAPIDAPI_HOST=twitter-api45.p.rapidapi.com

# Email (choose one method)
# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OR SendGrid
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=your-email@domain.com

# OR AWS SES (credentials via IAM)
SES_FROM_EMAIL=your-email@domain.com

# Notification recipient
NOTIFY_EMAIL=your-personal@email.com
```

## Step 5: Install Dependencies

```bash
pip install tweepy requests boto3
```

For minimal installation (RapidAPI + SMTP only):
```bash
pip install requests
```

## Step 6: Test Locally

```bash
python scripts/main.py --config config.json --email your@email.com
```

## Troubleshooting

### "No Twitter API credentials found"
- Ensure TWITTER_BEARER_TOKEN or RAPIDAPI_KEY is set
- Check for typos in environment variable names

### "No email credentials found"
- Ensure at least one email method is configured
- For Gmail, make sure you're using an App Password, not your regular password

### Rate limiting
- Official API: Check your tier limits
- RapidAPI: Check your subscription limits
- Consider reducing check frequency

### No alerts triggered
- Lower thresholds temporarily for testing
- Ensure keywords/accounts are active
- Check that tweets are recent (within 7 days)
