---
name: x-trending-monitor
description: |
  Monitor X/Twitter for high-engagement trending posts matching specific keywords or from followed accounts.
  This skill detects posts with rapid engagement growth (e.g., 1000+ likes/hour) or high absolute engagement
  (e.g., 5000+ total interactions), then sends email notifications. Use this skill when setting up
  automated X/Twitter monitoring for marketing, content opportunities, or trend detection.
---

# X/Twitter Trending Monitor

Automatically detect trending posts on X/Twitter and receive email notifications for timely engagement opportunities.

## Purpose

This skill enables automated discovery of high-engagement posts on X/Twitter for:
- Marketing teams seeking viral content opportunities
- Creators wanting to engage with trending topics
- Businesses monitoring industry conversations

## Triggering Conditions

This skill is triggered when users need to:
- Set up X/Twitter trend monitoring
- Configure alerts for high-engagement posts
- Deploy a serverless monitoring solution
- Customize keyword or account tracking

## Components

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/monitor.py` | Core monitoring logic - fetches tweets, tracks engagement, detects trends |
| `scripts/notifier.py` | Email notification system - supports SMTP, SendGrid, AWS SES |
| `scripts/main.py` | Entry point - orchestrates monitoring and notification, includes Lambda handler |

### Configuration

Copy `assets/config.template.json` to `config.json` and customize:

```json
{
  "keywords": ["AI", "data analytics", "your-topic"],
  "followed_accounts": ["username1", "username2"],
  "rapid_growth_threshold": 1000,
  "absolute_threshold": 5000
}
```

### Alert Types

1. **Rapid Growth**: Posts gaining engagement faster than `rapid_growth_threshold` per hour
2. **Threshold Reached**: Posts exceeding `absolute_threshold` total engagement

## Setup Workflow

### 1. Obtain Twitter API Access

To obtain API access, refer to `references/setup-guide.md` for detailed instructions.

Two options:
- **Official API**: Apply at developer.twitter.com ($100/mo for Basic tier)
- **RapidAPI**: Subscribe to twitter-api45 or similar (free/low-cost tiers available)

### 2. Configure Email Notifications

Supported providers (configure one):
- **Gmail SMTP**: Use App Password, set `SMTP_*` environment variables
- **SendGrid**: Set `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL`
- **AWS SES**: Set `SES_FROM_EMAIL` with IAM credentials

### 3. Set Environment Variables

Required:
```bash
# Twitter (choose one)
TWITTER_BEARER_TOKEN=xxx    # Official API
RAPIDAPI_KEY=xxx            # RapidAPI alternative

# Email (choose one)
SMTP_USER=xxx SMTP_PASSWORD=xxx    # Gmail
SENDGRID_API_KEY=xxx               # SendGrid

# Notification recipient
NOTIFY_EMAIL=your@email.com
```

### 4. Deploy

For deployment options (AWS Lambda, Vercel, GitHub Actions, etc.), refer to `references/deployment-guide.md`.

Quick start with GitHub Actions (free, no server needed):
1. Fork/create repository with this skill's files
2. Add secrets in repo settings
3. Enable the workflow in `.github/workflows/monitor.yml`

## Local Testing

```bash
# Install dependencies
pip install -r assets/requirements.txt

# Configure
cp assets/config.template.json config.json
# Edit config.json with your keywords and accounts

# Run
python scripts/main.py --email your@email.com
```

## Customization

### Adjusting Thresholds

Lower thresholds for testing or niche topics:
```json
{
  "rapid_growth_threshold": 100,
  "absolute_threshold": 500
}
```

### Adding Keywords

Focus on topics relevant to GBase and data analytics:
```json
{
  "keywords": [
    "data visualization",
    "business intelligence",
    "dashboard",
    "analytics tool",
    "数据可视化",
    "BI工具"
  ]
}
```

### Modifying Email Template

Edit `format_alert_email()` in `scripts/notifier.py` to customize the notification format.

## Responding to Alerts

When notified of a trending post:
1. Review the tweet content and engagement
2. Assess relevance to GBase's value proposition
3. Create a PPT-based response using GBase's presentation features
4. Reply to the tweet with valuable, non-promotional insights

## Limitations

- Twitter API rate limits apply (varies by tier)
- Free tiers have monthly tweet limits
- Engagement tracking requires persistent storage for accurate growth detection
- Some RapidAPI providers may have reliability issues
