#!/usr/bin/env python3
"""
X/Twitter Trending Monitor - Core Monitoring Script
Detects high-engagement posts based on keywords and followed accounts.
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import requests

# tweepy is optional - only needed for official Twitter API
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None


@dataclass
class Tweet:
    """Represents a tweet with engagement metrics."""
    id: str
    text: str
    author_id: str
    author_username: str
    created_at: datetime
    likes: int
    retweets: int
    replies: int
    quotes: int
    url: str

    @property
    def total_engagement(self) -> int:
        return self.likes + self.retweets + self.replies + self.quotes

    def to_dict(self) -> dict:
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        d['total_engagement'] = self.total_engagement
        return d


@dataclass
class TrendAlert:
    """Alert for a trending tweet."""
    tweet: Tweet
    alert_type: str  # 'rapid_growth' or 'threshold_reached'
    previous_engagement: Optional[int]
    current_engagement: int
    growth_rate: Optional[float]  # engagement per hour
    detected_at: datetime
    keyword_matched: Optional[str]

    def to_dict(self) -> dict:
        return {
            'tweet': self.tweet.to_dict(),
            'alert_type': self.alert_type,
            'previous_engagement': self.previous_engagement,
            'current_engagement': self.current_engagement,
            'growth_rate': self.growth_rate,
            'detected_at': self.detected_at.isoformat(),
            'keyword_matched': self.keyword_matched
        }


class TwitterDataSource(ABC):
    """Abstract base class for Twitter data sources."""

    @abstractmethod
    def search_tweets(self, query: str, max_results: int = 100) -> list[Tweet]:
        """Search for tweets matching a query."""
        pass

    @abstractmethod
    def get_user_tweets(self, username: str, max_results: int = 100) -> list[Tweet]:
        """Get recent tweets from a user."""
        pass

    @abstractmethod
    def get_tweet_by_id(self, tweet_id: str) -> Optional[Tweet]:
        """Get a specific tweet by ID."""
        pass


class OfficialTwitterAPI(TwitterDataSource):
    """Official Twitter API v2 implementation."""

    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token=bearer_token)
        self.tweet_fields = ['created_at', 'public_metrics', 'author_id']
        self.user_fields = ['username']
        self.expansions = ['author_id']

    def _parse_tweet(self, tweet, users_dict: dict) -> Tweet:
        author = users_dict.get(tweet.author_id, {})
        metrics = tweet.public_metrics or {}
        return Tweet(
            id=str(tweet.id),
            text=tweet.text,
            author_id=str(tweet.author_id),
            author_username=author.get('username', 'unknown'),
            created_at=tweet.created_at or datetime.utcnow(),
            likes=metrics.get('like_count', 0),
            retweets=metrics.get('retweet_count', 0),
            replies=metrics.get('reply_count', 0),
            quotes=metrics.get('quote_count', 0),
            url=f"https://x.com/{author.get('username', 'i')}/status/{tweet.id}"
        )

    def search_tweets(self, query: str, max_results: int = 100) -> list[Tweet]:
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=self.tweet_fields,
                user_fields=self.user_fields,
                expansions=self.expansions
            )

            if not response.data:
                return []

            users_dict = {}
            if response.includes and 'users' in response.includes:
                users_dict = {u.id: {'username': u.username} for u in response.includes['users']}

            return [self._parse_tweet(t, users_dict) for t in response.data]
        except Exception as e:
            print(f"Error searching tweets: {e}")
            return []

    def get_user_tweets(self, username: str, max_results: int = 100) -> list[Tweet]:
        try:
            user = self.client.get_user(username=username)
            if not user.data:
                return []

            response = self.client.get_users_tweets(
                id=user.data.id,
                max_results=min(max_results, 100),
                tweet_fields=self.tweet_fields,
                user_fields=self.user_fields,
                expansions=self.expansions
            )

            if not response.data:
                return []

            users_dict = {user.data.id: {'username': username}}
            return [self._parse_tweet(t, users_dict) for t in response.data]
        except Exception as e:
            print(f"Error getting user tweets: {e}")
            return []

    def get_tweet_by_id(self, tweet_id: str) -> Optional[Tweet]:
        try:
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=self.tweet_fields,
                user_fields=self.user_fields,
                expansions=self.expansions
            )

            if not response.data:
                return None

            users_dict = {}
            if response.includes and 'users' in response.includes:
                users_dict = {u.id: {'username': u.username} for u in response.includes['users']}

            return self._parse_tweet(response.data, users_dict)
        except Exception as e:
            print(f"Error getting tweet: {e}")
            return None


class RapidAPITwitter(TwitterDataSource):
    """RapidAPI Twitter alternative (twitter-api45 or similar)."""

    def __init__(self, api_key: str, api_host: str = "twitter-api45.p.rapidapi.com"):
        self.api_key = api_key
        self.api_host = api_host
        self.base_url = f"https://{api_host}"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host
        }

    def _parse_tweet(self, data: dict, fallback_username: str = None) -> Tweet:
        # Get username from data or use fallback (for timeline API which doesn't return screen_name)
        username = data.get('screen_name') or data.get('username') or fallback_username or 'unknown'
        return Tweet(
            id=str(data.get('tweet_id') or data.get('id', '')),
            text=data.get('text', ''),
            author_id=str(data.get('user_id', '')),
            author_username=username,
            created_at=datetime.strptime(data['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                       if 'created_at' in data else datetime.utcnow(),
            likes=int(data.get('favorites') or data.get('like_count', 0)),
            retweets=int(data.get('retweets') or data.get('retweet_count', 0)),
            replies=int(data.get('replies') or data.get('reply_count', 0)),
            quotes=int(data.get('quotes') or data.get('quote_count', 0)),
            url=f"https://x.com/{username}/status/{data.get('tweet_id', data.get('id', ''))}"
        )

    def search_tweets(self, query: str, max_results: int = 100) -> list[Tweet]:
        try:
            response = requests.get(
                f"{self.base_url}/search.php",
                headers=self.headers,
                params={"query": query, "search_type": "Latest"}
            )
            response.raise_for_status()
            data = response.json()

            tweets = data.get('timeline', []) or data.get('tweets', [])
            return [self._parse_tweet(t) for t in tweets[:max_results]]
        except Exception as e:
            print(f"Error searching tweets via RapidAPI: {e}")
            return []

    def get_user_tweets(self, username: str, max_results: int = 100) -> list[Tweet]:
        try:
            response = requests.get(
                f"{self.base_url}/timeline.php",
                headers=self.headers,
                params={"screenname": username}
            )
            response.raise_for_status()
            data = response.json()

            tweets = data.get('timeline', []) or data.get('tweets', [])
            # Pass username as fallback since timeline API doesn't return screen_name
            return [self._parse_tweet(t, fallback_username=username) for t in tweets[:max_results]]
        except Exception as e:
            print(f"Error getting user tweets via RapidAPI: {e}")
            return []

    def get_tweet_by_id(self, tweet_id: str) -> Optional[Tweet]:
        try:
            response = requests.get(
                f"{self.base_url}/tweet.php",
                headers=self.headers,
                params={"id": tweet_id}
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_tweet(data)
        except Exception as e:
            print(f"Error getting tweet via RapidAPI: {e}")
            return None


class EngagementTracker:
    """Tracks tweet engagement over time to detect rapid growth."""

    def __init__(self, storage_path: str = "engagement_history.json"):
        self.storage_path = storage_path
        self.history = self._load_history()

    def _load_history(self) -> dict:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_history(self):
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def record_engagement(self, tweet: Tweet):
        """Record current engagement for a tweet."""
        if tweet.id not in self.history:
            self.history[tweet.id] = {
                'first_seen': datetime.utcnow().isoformat(),
                'records': []
            }

        self.history[tweet.id]['records'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'engagement': tweet.total_engagement,
            'likes': tweet.likes,
            'retweets': tweet.retweets
        })

        # Keep only last 24 hours of records
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        self.history[tweet.id]['records'] = [
            r for r in self.history[tweet.id]['records']
            if r['timestamp'] > cutoff
        ]

        self._save_history()

    def get_growth_rate(self, tweet_id: str) -> Optional[tuple[int, float]]:
        """Get previous engagement and growth rate (per hour) for a tweet."""
        if tweet_id not in self.history:
            return None

        records = self.history[tweet_id]['records']
        if len(records) < 2:
            return None

        # Compare with oldest record in history
        oldest = records[0]
        newest = records[-1]

        prev_engagement = oldest['engagement']
        curr_engagement = newest['engagement']

        time_diff = (
            datetime.fromisoformat(newest['timestamp']) -
            datetime.fromisoformat(oldest['timestamp'])
        ).total_seconds() / 3600  # hours

        if time_diff < 0.1:  # Less than 6 minutes
            return None

        growth_rate = (curr_engagement - prev_engagement) / time_diff
        return prev_engagement, growth_rate

    def cleanup_old_entries(self, max_age_hours: int = 48):
        """Remove entries older than max_age_hours."""
        cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
        to_remove = []

        for tweet_id, data in self.history.items():
            if data['first_seen'] < cutoff and not data['records']:
                to_remove.append(tweet_id)

        for tweet_id in to_remove:
            del self.history[tweet_id]

        self._save_history()


class TrendingMonitor:
    """Main monitoring class that orchestrates the detection process."""

    def __init__(
        self,
        data_source: TwitterDataSource,
        keywords: list[str],
        followed_accounts: list[str],
        rapid_growth_threshold: int = 1000,  # engagement per hour
        absolute_threshold: int = 5000,  # total engagement
        storage_path: str = "engagement_history.json"
    ):
        self.data_source = data_source
        self.keywords = keywords
        self.followed_accounts = followed_accounts
        self.rapid_growth_threshold = rapid_growth_threshold
        self.absolute_threshold = absolute_threshold
        self.tracker = EngagementTracker(storage_path)
        self.alerted_tweets: set[str] = set()

    def _load_alerted(self, path: str = "alerted_tweets.json"):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Only keep alerts from last 7 days
                    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
                    self.alerted_tweets = set(
                        k for k, v in data.items() if v > cutoff
                    )
            except:
                pass

    def _save_alerted(self, path: str = "alerted_tweets.json"):
        data = {tid: datetime.utcnow().isoformat() for tid in self.alerted_tweets}
        with open(path, 'w') as f:
            json.dump(data, f)

    def check_tweet(self, tweet: Tweet, keyword: Optional[str] = None) -> Optional[TrendAlert]:
        """Check if a tweet meets alerting criteria."""
        # Skip if already alerted
        if tweet.id in self.alerted_tweets:
            return None

        # Record current engagement
        self.tracker.record_engagement(tweet)

        # Check absolute threshold
        if tweet.total_engagement >= self.absolute_threshold:
            return TrendAlert(
                tweet=tweet,
                alert_type='threshold_reached',
                previous_engagement=None,
                current_engagement=tweet.total_engagement,
                growth_rate=None,
                detected_at=datetime.utcnow(),
                keyword_matched=keyword
            )

        # Check rapid growth
        growth_data = self.tracker.get_growth_rate(tweet.id)
        if growth_data:
            prev_engagement, growth_rate = growth_data
            if growth_rate >= self.rapid_growth_threshold:
                return TrendAlert(
                    tweet=tweet,
                    alert_type='rapid_growth',
                    previous_engagement=prev_engagement,
                    current_engagement=tweet.total_engagement,
                    growth_rate=growth_rate,
                    detected_at=datetime.utcnow(),
                    keyword_matched=keyword
                )

        return None

    def run_check(self) -> list[TrendAlert]:
        """Run a complete check cycle and return any alerts."""
        alerts = []
        self._load_alerted()

        # Check keyword searches
        for keyword in self.keywords:
            print(f"Searching for keyword: {keyword}")
            tweets = self.data_source.search_tweets(keyword)
            for tweet in tweets:
                alert = self.check_tweet(tweet, keyword=keyword)
                if alert:
                    alerts.append(alert)
                    self.alerted_tweets.add(tweet.id)

        # Check followed accounts
        for username in self.followed_accounts:
            print(f"Checking account: @{username}")
            tweets = self.data_source.get_user_tweets(username)
            for tweet in tweets:
                alert = self.check_tweet(tweet)
                if alert:
                    alerts.append(alert)
                    self.alerted_tweets.add(tweet.id)

        self._save_alerted()
        self.tracker.cleanup_old_entries()

        return alerts


def create_data_source() -> TwitterDataSource:
    """Create appropriate data source based on environment variables."""
    # Try official API first (requires tweepy)
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    if bearer_token and TWEEPY_AVAILABLE:
        print("Using Official Twitter API v2")
        return OfficialTwitterAPI(bearer_token)

    # Try RapidAPI
    rapidapi_key = os.environ.get('RAPIDAPI_KEY')
    if rapidapi_key:
        api_host = os.environ.get('RAPIDAPI_HOST', 'twitter-api45.p.rapidapi.com')
        print(f"Using RapidAPI: {api_host}")
        return RapidAPITwitter(rapidapi_key, api_host)

    raise ValueError(
        "No Twitter API credentials found. Set either:\n"
        "  - TWITTER_BEARER_TOKEN for official API\n"
        "  - RAPIDAPI_KEY for RapidAPI alternative"
    )


def load_config(config_path: str = "config.json") -> dict:
    """Load monitoring configuration."""
    default_config = {
        "keywords": ["AI", "GPT", "LLM", "data analytics"],
        "followed_accounts": [],
        "rapid_growth_threshold": 1000,
        "absolute_threshold": 5000,
        "check_interval_minutes": 15
    }

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            default_config.update(user_config)

    return default_config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="X/Twitter Trending Monitor")
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--output', default='alerts.json', help='Output file for alerts')
    args = parser.parse_args()

    config = load_config(args.config)
    data_source = create_data_source()

    monitor = TrendingMonitor(
        data_source=data_source,
        keywords=config['keywords'],
        followed_accounts=config['followed_accounts'],
        rapid_growth_threshold=config['rapid_growth_threshold'],
        absolute_threshold=config['absolute_threshold']
    )

    print(f"Starting monitoring check at {datetime.utcnow().isoformat()}")
    alerts = monitor.run_check()

    if alerts:
        print(f"\nFound {len(alerts)} trending tweets!")
        alerts_data = [a.to_dict() for a in alerts]

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, ensure_ascii=False, indent=2)

        for alert in alerts:
            print(f"\n{'='*60}")
            print(f"Type: {alert.alert_type}")
            print(f"Tweet: {alert.tweet.url}")
            print(f"Engagement: {alert.current_engagement}")
            if alert.growth_rate:
                print(f"Growth Rate: {alert.growth_rate:.0f}/hour")
            print(f"Text: {alert.tweet.text[:200]}...")
    else:
        print("No trending tweets detected.")
