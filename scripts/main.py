#!/usr/bin/env python3
"""
Main entry point for X/Twitter Trending Monitor
Combines monitoring and notification into a single execution flow.
"""

import os
import json
import sys
from datetime import datetime

# Add scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from monitor import TrendingMonitor, create_data_source, load_config
from notifier import send_alert_notification


def run_monitor(config_path: str = None, notify_email: str = None) -> dict:
    """
    Run the complete monitoring cycle.

    Args:
        config_path: Path to config.json (optional, uses default if not provided)
        notify_email: Email to send notifications to (optional, uses env var if not provided)

    Returns:
        dict with 'alerts' and 'success' keys
    """
    # Load configuration
    config_path = config_path or os.environ.get('CONFIG_PATH', 'config.json')
    config = load_config(config_path)

    # Get notification email
    notify_email = notify_email or os.environ.get('NOTIFY_EMAIL')

    print(f"[{datetime.utcnow().isoformat()}] Starting monitoring cycle")
    print(f"Keywords: {config['keywords']}")
    print(f"Followed accounts: {config['followed_accounts']}")

    try:
        # Create data source and monitor
        data_source = create_data_source()
        monitor = TrendingMonitor(
            data_source=data_source,
            keywords=config['keywords'],
            followed_accounts=config['followed_accounts'],
            rapid_growth_threshold=config.get('rapid_growth_threshold', 1000),
            absolute_threshold=config.get('absolute_threshold', 5000)
        )

        # Run the check
        alerts = monitor.run_check()
        alerts_data = [a.to_dict() for a in alerts]

        print(f"Found {len(alerts)} trending tweets")

        # Send notification if there are alerts and email is configured
        notification_sent = False
        if alerts_data and notify_email:
            print(f"Sending notification to {notify_email}")
            notification_sent = send_alert_notification(alerts_data, notify_email)

        return {
            'success': True,
            'alerts_count': len(alerts_data),
            'alerts': alerts_data,
            'notification_sent': notification_sent,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error during monitoring: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda entry point."""
    config_path = event.get('config_path') or os.environ.get('CONFIG_PATH')
    notify_email = event.get('notify_email') or os.environ.get('NOTIFY_EMAIL')

    result = run_monitor(config_path, notify_email)

    return {
        'statusCode': 200 if result['success'] else 500,
        'body': json.dumps(result, ensure_ascii=False)
    }


# Vercel/Netlify serverless handler
def handler(request):
    """Vercel/Netlify serverless function entry point."""
    result = run_monitor()
    return {
        'statusCode': 200 if result['success'] else 500,
        'body': json.dumps(result, ensure_ascii=False),
        'headers': {'Content-Type': 'application/json'}
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="X/Twitter Trending Monitor")
    parser.add_argument('--config', help='Path to config.json')
    parser.add_argument('--email', help='Email to send notifications to')
    args = parser.parse_args()

    result = run_monitor(args.config, args.email)

    print("\n" + "=" * 60)
    print(f"Monitoring completed: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Alerts found: {result.get('alerts_count', 0)}")
    print(f"Notification sent: {result.get('notification_sent', False)}")

    if result.get('alerts'):
        print("\nAlert details:")
        for alert in result['alerts']:
            print(f"  - {alert['alert_type']}: {alert['tweet']['url']}")
