# Serverless Deployment Guide

Deploy the X/Twitter Trending Monitor as a scheduled serverless function.

## Option 1: AWS Lambda + EventBridge (Recommended)

### Prerequisites
- AWS Account
- AWS CLI configured
- Python 3.9+

### Step 1: Create Deployment Package

```bash
# Create deployment directory
mkdir lambda-package
cd lambda-package

# Install dependencies
pip install tweepy requests -t .

# Copy scripts
cp ../scripts/*.py .

# Create zip
zip -r ../deployment.zip .
```

### Step 2: Create Lambda Function

```bash
# Create function
aws lambda create-function \
  --function-name x-trending-monitor \
  --runtime python3.11 \
  --handler main.lambda_handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --timeout 120 \
  --memory-size 256

# Set environment variables
aws lambda update-function-configuration \
  --function-name x-trending-monitor \
  --environment "Variables={
    TWITTER_BEARER_TOKEN=your-token,
    SES_FROM_EMAIL=alerts@yourdomain.com,
    NOTIFY_EMAIL=your@email.com
  }"
```

### Step 3: Create EventBridge Schedule

```bash
# Create rule to run every 15 minutes
aws events put-rule \
  --name x-monitor-schedule \
  --schedule-expression "rate(15 minutes)"

# Add Lambda as target
aws events put-targets \
  --rule x-monitor-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:x-trending-monitor"
```

### Step 4: Add S3 for State (Optional but Recommended)

Store engagement history in S3 for persistence across invocations:

```python
# Add to main.py for S3 state management
import boto3

def get_state_from_s3(bucket, key):
    s3 = boto3.client('s3')
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj['Body'].read())
    except:
        return {}

def save_state_to_s3(bucket, key, state):
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(state),
        ContentType='application/json'
    )
```

---

## Option 2: Vercel (Simple, Free Tier Available)

### Step 1: Project Structure

```
x-trending-monitor/
├── api/
│   └── monitor.py      # Serverless function
├── scripts/
│   ├── monitor.py
│   └── notifier.py
├── vercel.json
└── requirements.txt
```

### Step 2: Create API Endpoint

Create `api/monitor.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from main import run_monitor
import json

def handler(request):
    result = run_monitor()
    return {
        'statusCode': 200 if result['success'] else 500,
        'body': json.dumps(result)
    }
```

### Step 3: Create vercel.json

```json
{
  "version": 2,
  "builds": [
    { "src": "api/*.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/monitor", "dest": "/api/monitor.py" }
  ],
  "crons": [
    {
      "path": "/api/monitor",
      "schedule": "*/15 * * * *"
    }
  ]
}
```

### Step 4: Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
```

---

## Option 3: GitHub Actions (Free, No Server Needed)

### Step 1: Create Workflow

Create `.github/workflows/monitor.yml`:

```yaml
name: X Trending Monitor

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Allow manual trigger

jobs:
  monitor:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install tweepy requests

      - name: Download state
        uses: actions/cache@v4
        with:
          path: |
            engagement_history.json
            alerted_tweets.json
          key: monitor-state-${{ github.run_id }}
          restore-keys: monitor-state-

      - name: Run monitor
        env:
          TWITTER_BEARER_TOKEN: ${{ secrets.TWITTER_BEARER_TOKEN }}
          SMTP_HOST: smtp.gmail.com
          SMTP_PORT: 587
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          NOTIFY_EMAIL: ${{ secrets.NOTIFY_EMAIL }}
        run: python scripts/main.py

      - name: Upload state
        uses: actions/upload-artifact@v4
        with:
          name: monitor-state
          path: |
            engagement_history.json
            alerted_tweets.json
```

### Step 2: Add Secrets

In GitHub repo Settings → Secrets → Actions, add:
- TWITTER_BEARER_TOKEN
- SMTP_USER
- SMTP_PASSWORD
- NOTIFY_EMAIL

---

## Option 4: Railway / Render (Simple PaaS)

### Step 1: Add Procfile

```
worker: python scripts/main.py
```

### Step 2: Add requirements.txt

```
tweepy>=4.14.0
requests>=2.31.0
```

### Step 3: Add Scheduler

Both Railway and Render support cron jobs in their dashboard.
Set schedule to `*/15 * * * *` for every 15 minutes.

---

## State Management Across Invocations

Serverless functions are stateless. To track engagement over time:

### Option A: DynamoDB (AWS)
```python
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('x-monitor-state')
# Use table.get_item() and table.put_item()
```

### Option B: Redis (Vercel, Railway)
```python
import redis
r = redis.from_url(os.environ['REDIS_URL'])
# Use r.get() and r.set()
```

### Option C: SQLite + S3 (Simple)
- Download state file from S3 at start
- Upload state file to S3 at end

### Option D: GitHub Actions Cache (Free)
- Uses built-in cache action as shown above
- Limited to 10GB, cleared after 7 days of no access

---

## Cost Comparison

| Platform | Free Tier | Estimated Monthly Cost |
|----------|-----------|----------------------|
| AWS Lambda | 1M requests | $0-5 |
| Vercel | 100GB-hrs | $0 (hobby) |
| GitHub Actions | 2000 min/mo | $0 |
| Railway | $5 credit | $0-5 |
| Render | 750 hrs | $0 |

For this use case (running every 15 min), all options fit within free tiers.
