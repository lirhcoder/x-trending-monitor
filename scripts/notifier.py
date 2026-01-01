#!/usr/bin/env python3
"""
Email Notification Module for X/Twitter Trending Monitor
Supports multiple email providers: SMTP, SendGrid, AWS SES
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


class TrendAlert:
    """Simplified TrendAlert for notification purposes."""
    def __init__(self, data: dict):
        self.tweet = data.get('tweet', {})
        self.alert_type = data.get('alert_type', 'unknown')
        self.previous_engagement = data.get('previous_engagement')
        self.current_engagement = data.get('current_engagement', 0)
        self.growth_rate = data.get('growth_rate')
        self.detected_at = data.get('detected_at', '')
        self.keyword_matched = data.get('keyword_matched')


class EmailNotifier(ABC):
    """Abstract base class for email notifications."""

    @abstractmethod
    def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send an email notification."""
        pass


class SMTPNotifier(EmailNotifier):
    """SMTP-based email notifier (Gmail, Outlook, etc.)."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: Optional[str] = None,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.use_tls = use_tls

    def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            server.login(self.username, self.password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()

            print(f"Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False


class SendGridNotifier(EmailNotifier):
    """SendGrid email notifier."""

    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email

    def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        try:
            import requests

            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.from_email},
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": text_body},
                        {"type": "text/html", "value": html_body}
                    ]
                }
            )
            response.raise_for_status()
            print(f"Email sent via SendGrid to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email via SendGrid: {e}")
            return False


class AWSSESNotifier(EmailNotifier):
    """AWS SES email notifier."""

    def __init__(self, from_email: str, region: str = "us-east-1"):
        self.from_email = from_email
        self.region = region

    def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        try:
            import boto3

            ses = boto3.client('ses', region_name=self.region)
            response = ses.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )
            print(f"Email sent via AWS SES to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email via AWS SES: {e}")
            return False


def create_notifier() -> EmailNotifier:
    """Create appropriate notifier based on environment variables."""
    # Try SendGrid first
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if sendgrid_key:
        from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@example.com')
        return SendGridNotifier(sendgrid_key, from_email)

    # Try AWS SES
    if os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        from_email = os.environ.get('SES_FROM_EMAIL', 'noreply@example.com')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        return AWSSESNotifier(from_email, region)

    # Fall back to SMTP
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASSWORD')

    if smtp_user and smtp_pass:
        return SMTPNotifier(smtp_host, smtp_port, smtp_user, smtp_pass)

    raise ValueError(
        "No email credentials found. Set one of:\n"
        "  - SENDGRID_API_KEY + SENDGRID_FROM_EMAIL\n"
        "  - AWS credentials + SES_FROM_EMAIL\n"
        "  - SMTP_HOST + SMTP_PORT + SMTP_USER + SMTP_PASSWORD"
    )


def format_alert_email(alerts: list[TrendAlert]) -> tuple[str, str, str]:
    """Format alerts into email subject and body (HTML + text)."""
    subject = f"[X Monitor] {len(alerts)} Trending Post(s) Detected!"

    # Build HTML email
    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .alert { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 16px 0; }
                .alert-rapid { border-left: 4px solid #f59e0b; }
                .alert-threshold { border-left: 4px solid #10b981; }
                .alert-type { font-size: 12px; color: #666; text-transform: uppercase; }
                .tweet-text { font-size: 16px; margin: 12px 0; }
                .metrics { display: flex; gap: 16px; color: #666; }
                .metric { display: flex; align-items: center; gap: 4px; }
                .tweet-link { color: #1d9bf0; text-decoration: none; }
                .action-hint { background: #f3f4f6; padding: 12px; border-radius: 6px; margin-top: 16px; }
            </style>
        </head>
        <body>
            <h2>X/Twitter Trending Alert</h2>
            <p>The following posts have triggered your monitoring rules:</p>
        """
    ]

    text_parts = [
        "X/Twitter Trending Alert\n",
        "=" * 40 + "\n\n",
        f"Found {len(alerts)} trending post(s):\n\n"
    ]

    for i, alert in enumerate(alerts, 1):
        tweet = alert.tweet
        alert_class = "alert-rapid" if alert.alert_type == 'rapid_growth' else "alert-threshold"
        alert_label = "Rapid Growth" if alert.alert_type == 'rapid_growth' else "Threshold Reached"

        html_parts.append(f"""
            <div class="alert {alert_class}">
                <div class="alert-type">{alert_label}</div>
                <p class="tweet-text">{tweet.get('text', '')[:280]}</p>
                <div class="metrics">
                    <span class="metric">Likes: {tweet.get('likes', 0):,}</span>
                    <span class="metric">Retweets: {tweet.get('retweets', 0):,}</span>
                    <span class="metric">Total: {alert.current_engagement:,}</span>
        """)

        if alert.growth_rate:
            html_parts.append(f"""
                    <span class="metric">Growth: {alert.growth_rate:,.0f}/hour</span>
            """)

        html_parts.append(f"""
                </div>
                <p>
                    <a href="{tweet.get('url', '#')}" class="tweet-link">View on X</a>
                    {f' | Matched: "{alert.keyword_matched}"' if alert.keyword_matched else ''}
                </p>
            </div>
        """)

        # Text version
        text_parts.append(f"#{i} [{alert_label}]\n")
        text_parts.append(f"{tweet.get('text', '')[:200]}...\n")
        text_parts.append(f"Engagement: {alert.current_engagement:,}\n")
        if alert.growth_rate:
            text_parts.append(f"Growth Rate: {alert.growth_rate:,.0f}/hour\n")
        text_parts.append(f"Link: {tweet.get('url', 'N/A')}\n")
        if alert.keyword_matched:
            text_parts.append(f"Matched keyword: {alert.keyword_matched}\n")
        text_parts.append("\n" + "-" * 40 + "\n\n")

    html_parts.append("""
            <div class="action-hint">
                <strong>Suggested Action:</strong> Create a GBase PPT response to engage with this trending topic!
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">
                Sent by X Trending Monitor |
                <a href="#">Unsubscribe</a>
            </p>
        </body>
        </html>
    """)

    text_parts.append("\nSuggested Action: Create a GBase PPT response!\n")

    return subject, ''.join(html_parts), ''.join(text_parts)


def send_alert_notification(alerts: list[dict], to_email: str) -> bool:
    """Send notification for detected alerts."""
    if not alerts:
        print("No alerts to send.")
        return True

    alert_objects = [TrendAlert(a) for a in alerts]
    subject, html_body, text_body = format_alert_email(alert_objects)

    notifier = create_notifier()
    return notifier.send(to_email, subject, html_body, text_body)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send notification for trending alerts")
    parser.add_argument('--alerts', required=True, help='Path to alerts JSON file')
    parser.add_argument('--email', required=True, help='Recipient email address')
    args = parser.parse_args()

    with open(args.alerts, 'r', encoding='utf-8') as f:
        alerts = json.load(f)

    success = send_alert_notification(alerts, args.email)
    exit(0 if success else 1)
