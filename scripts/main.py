#!/usr/bin/env python3
"""
X/Twitter Trending Monitor - Main Entry Point
V2: Dashboard generation with AI analysis and recommendations.
"""

import os
import sys
import json
from datetime import datetime, timezone

# Add scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from monitor import TrendingMonitor, create_data_source, load_config
from notifier import send_alert_notification

# Import v2 components (optional)
try:
    from analyzer import create_analyzer, GeminiAnalyzer
    from html_generator import generate_dashboard_html, generate_json_data
    AI_AVAILABLE = True
except ImportError as e:
    print(f"AI components not available: {e}")
    AI_AVAILABLE = False


def run_monitor_v1(config_path: str = None, notify_email: str = None) -> dict:
    """
    V1: Monitor and send email notifications.
    """
    config_path = config_path or os.environ.get('CONFIG_PATH', 'config.json')
    config = load_config(config_path)
    notify_email = notify_email or os.environ.get('NOTIFY_EMAIL')

    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] Starting monitoring cycle (V1 - Email)")
    print(f"Keywords: {config['keywords']}")
    print(f"Followed accounts: {config['followed_accounts']}")

    try:
        data_source = create_data_source()
        monitor = TrendingMonitor(
            data_source=data_source,
            keywords=config['keywords'],
            followed_accounts=config['followed_accounts'],
            rapid_growth_threshold=config.get('rapid_growth_threshold', 1000),
            absolute_threshold=config.get('absolute_threshold', 5000)
        )

        alerts = monitor.run_check()
        alerts_data = [a.to_dict() for a in alerts]

        print(f"Found {len(alerts)} trending tweets")

        notification_sent = False
        if alerts_data and notify_email:
            print(f"Sending notification to {notify_email}")
            notification_sent = send_alert_notification(alerts_data, notify_email)

        return {
            'success': True,
            'alerts_count': len(alerts_data),
            'alerts': alerts_data,
            'notification_sent': notification_sent,
            'timestamp': now.isoformat()
        }

    except Exception as e:
        print(f"Error during monitoring: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


def run_monitor_v2(config_path: str = None, output_dir: str = "docs") -> dict:
    """
    V2: Monitor, analyze with AI, and generate dashboard.
    """
    if not AI_AVAILABLE:
        print("AI components not available. Falling back to V1.")
        return run_monitor_v1(config_path)

    config_path = config_path or os.environ.get('CONFIG_PATH', 'config.json')
    config = load_config(config_path)

    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] Starting monitoring cycle (V2 - Dashboard)")
    print(f"Keywords: {config['keywords']}")
    print(f"Followed accounts: {config['followed_accounts']}")

    try:
        # Step 1: Fetch tweets
        data_source = create_data_source()
        monitor = TrendingMonitor(
            data_source=data_source,
            keywords=config['keywords'],
            followed_accounts=config['followed_accounts'],
            rapid_growth_threshold=config.get('rapid_growth_threshold', 1000),
            absolute_threshold=config.get('absolute_threshold', 5000)
        )

        alerts = monitor.run_check()
        print(f"Found {len(alerts)} trending tweets")

        if not alerts:
            print("No trending tweets found. Generating empty dashboard.")
            generate_dashboard_html([], os.path.join(output_dir, "dashboard.html"), now)
            return {
                'success': True,
                'tweets_found': 0,
                'analyzed': 0,
                'dashboard_generated': True,
                'timestamp': now.isoformat()
            }

        # Step 2: Prepare tweets for analysis
        tweets_for_analysis = [
            {
                'id': a.tweet.id,
                'text': a.tweet.text,
                'author_username': a.tweet.author_username,
                'total_engagement': a.tweet.total_engagement,
                'url': a.tweet.url
            }
            for a in alerts
        ]

        # Step 3: Analyze with AI
        print("Analyzing tweets with Google Gemini...")
        analyzer = create_analyzer()
        analyzed_tweets = analyzer.analyze_tweets(tweets_for_analysis)

        print(f"Analyzed {len(analyzed_tweets)} tweets")

        # Show top recommendations
        print("\nTop recommendations:")
        for t in analyzed_tweets[:5]:
            print(f"  #{t.priority_rank} @{t.author_username} - {t.recommended_action}")
            print(f"     Relevance: {t.relevance_score}/10, Potential: {t.engagement_potential}/10")

        # Step 4: Generate dashboard
        analyzed_data = [t.to_dict() for t in analyzed_tweets]

        dashboard_path = os.path.join(output_dir, "dashboard.html")
        generate_dashboard_html(analyzed_data, dashboard_path, now)

        json_path = os.path.join(output_dir, "data.json")
        generate_json_data(analyzed_data, json_path)

        return {
            'success': True,
            'tweets_found': len(alerts),
            'analyzed': len(analyzed_tweets),
            'high_priority': len([t for t in analyzed_tweets if t.recommended_action == '高优先级回复']),
            'recommended': len([t for t in analyzed_tweets if t.recommended_action == '建议回复']),
            'dashboard_path': dashboard_path,
            'timestamp': now.isoformat()
        }

    except Exception as e:
        print(f"Error during V2 monitoring: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


def run_monitor(config_path: str = None, notify_email: str = None, mode: str = None) -> dict:
    """
    Main entry point. Chooses mode based on environment or parameter.
    """
    mode = mode or os.environ.get('MONITOR_MODE', 'v2')

    if mode == 'v1':
        return run_monitor_v1(config_path, notify_email)
    else:
        return run_monitor_v2(config_path)


# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda entry point."""
    mode = event.get('mode', 'v2')
    result = run_monitor(mode=mode)
    return {
        'statusCode': 200 if result['success'] else 500,
        'body': json.dumps(result, ensure_ascii=False)
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="X/Twitter Trending Monitor")
    parser.add_argument('--config', help='Path to config.json')
    parser.add_argument('--email', help='Email for V1 notifications')
    parser.add_argument('--mode', choices=['v1', 'v2'], default='v2',
                        help='v1=email notifications, v2=dashboard generation')
    parser.add_argument('--output', default='docs', help='Output directory for dashboard')
    args = parser.parse_args()

    if args.mode == 'v1':
        result = run_monitor_v1(args.config, args.email)
    else:
        result = run_monitor_v2(args.config, args.output)

    print("\n" + "=" * 60)
    print(f"Monitoring completed: {'SUCCESS' if result['success'] else 'FAILED'}")

    if result.get('tweets_found') is not None:
        print(f"Tweets found: {result.get('tweets_found', 0)}")
        print(f"Analyzed: {result.get('analyzed', 0)}")
        print(f"High priority: {result.get('high_priority', 0)}")
        print(f"Dashboard: {result.get('dashboard_path', 'N/A')}")
    else:
        print(f"Alerts found: {result.get('alerts_count', 0)}")
        print(f"Notification sent: {result.get('notification_sent', False)}")
