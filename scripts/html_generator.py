#!/usr/bin/env python3
"""
HTML Generator for X/Twitter Trending Dashboard
Creates a static webpage displaying analyzed tweets with recommendations.
"""

import os
import json
from datetime import datetime
from typing import Optional


def generate_dashboard_html(
    analyzed_tweets: list[dict],
    output_path: str = "docs/dashboard.html",
    last_updated: Optional[datetime] = None
) -> str:
    """Generate HTML dashboard for analyzed tweets."""

    if last_updated is None:
        last_updated = datetime.utcnow()

    # Group tweets by recommendation (removed "仅观察" category to save tokens)
    high_priority = [t for t in analyzed_tweets if t.get('recommended_action') == '高优先级回复']
    recommended = [t for t in analyzed_tweets if t.get('recommended_action') == '建议回复']
    optional = [t for t in analyzed_tweets if t.get('recommended_action') in ['可选回复', '分析失败']]

    def tweet_card(tweet: dict, show_rank: bool = True) -> str:
        """Generate HTML for a single tweet card."""
        action = tweet.get('recommended_action', '未知')
        action_class = {
            '高优先级回复': 'priority-high',
            '建议回复': 'priority-medium',
            '可选回复': 'priority-low',
            '仅观察': 'priority-observe'
        }.get(action, 'priority-observe')

        relevance = tweet.get('relevance_score', 0)
        potential = tweet.get('engagement_potential', 0)

        return f"""
        <div class="tweet-card {action_class}">
            <div class="tweet-header">
                <div class="tweet-author">
                    <span class="author-name">@{tweet.get('author_username', 'unknown')}</span>
                    {f'<span class="rank">#{tweet.get("priority_rank", "")}</span>' if show_rank else ''}
                </div>
                <div class="tweet-meta">
                    <span class="engagement">{tweet.get('engagement', 0):,} 互动</span>
                    <span class="action-badge {action_class}">{action}</span>
                </div>
            </div>

            <div class="tweet-content">
                <div class="translated-text">{tweet.get('translated_text', '')}</div>
                <details class="original-text">
                    <summary>查看原文</summary>
                    <p>{tweet.get('original_text', '')}</p>
                </details>
            </div>

            <div class="tweet-analysis">
                <div class="scores">
                    <div class="score">
                        <span class="score-label">相关度</span>
                        <div class="score-bar">
                            <div class="score-fill relevance" style="width: {relevance * 10}%"></div>
                        </div>
                        <span class="score-value">{relevance}/10</span>
                    </div>
                    <div class="score">
                        <span class="score-label">互动潜力</span>
                        <div class="score-bar">
                            <div class="score-fill potential" style="width: {potential * 10}%"></div>
                        </div>
                        <span class="score-value">{potential}/10</span>
                    </div>
                </div>

                <div class="reasoning">
                    <strong>分析理由：</strong>{tweet.get('reasoning', '无')}
                </div>

                {f'<div class="reply-suggestion"><strong>回复建议：</strong>{tweet.get("suggested_reply_angle", "")}</div>' if tweet.get('suggested_reply_angle') else ''}
            </div>

            <div class="tweet-actions">
                <a href="{tweet.get('url', '#')}" target="_blank" class="btn btn-primary">查看原帖</a>
            </div>
        </div>
        """

    def tweet_section(title: str, tweets: list[dict], section_class: str) -> str:
        """Generate HTML for a section of tweets."""
        if not tweets:
            return ""

        return f"""
        <section class="tweet-section {section_class}">
            <h2>{title} <span class="count">({len(tweets)})</span></h2>
            <div class="tweets-grid">
                {''.join(tweet_card(t) for t in tweets)}
            </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X热门帖子监控 - Sparticle营销助手</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        header h1 {{
            color: #1d9bf0;
            font-size: 28px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        header h1 svg {{
            width: 32px;
            height: 32px;
        }}

        .header-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #666;
            font-size: 14px;
        }}

        .stats {{
            display: flex;
            gap: 24px;
            margin-top: 16px;
        }}

        .stat {{
            background: #f8f9fa;
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}

        .stat-label {{
            font-size: 12px;
            color: #666;
        }}

        .stat.high .stat-value {{ color: #dc3545; }}
        .stat.medium .stat-value {{ color: #fd7e14; }}
        .stat.low .stat-value {{ color: #28a745; }}

        .tweet-section {{
            margin-bottom: 32px;
        }}

        .tweet-section h2 {{
            color: white;
            font-size: 20px;
            margin-bottom: 16px;
            padding-left: 8px;
            border-left: 4px solid white;
        }}

        .tweet-section h2 .count {{
            opacity: 0.7;
            font-weight: normal;
        }}

        .tweets-grid {{
            display: grid;
            gap: 16px;
        }}

        .tweet-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            border-left: 4px solid #ccc;
        }}

        .tweet-card.priority-high {{ border-left-color: #dc3545; }}
        .tweet-card.priority-medium {{ border-left-color: #fd7e14; }}
        .tweet-card.priority-low {{ border-left-color: #28a745; }}
        .tweet-card.priority-observe {{ border-left-color: #6c757d; }}

        .tweet-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}

        .tweet-author {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .author-name {{
            font-weight: 600;
            color: #1d9bf0;
        }}

        .rank {{
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}

        .tweet-meta {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .engagement {{
            color: #666;
            font-size: 14px;
        }}

        .action-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}

        .action-badge.priority-high {{ background: #f8d7da; color: #721c24; }}
        .action-badge.priority-medium {{ background: #fff3cd; color: #856404; }}
        .action-badge.priority-low {{ background: #d4edda; color: #155724; }}
        .action-badge.priority-observe {{ background: #e2e3e5; color: #383d41; }}

        .tweet-content {{
            margin-bottom: 16px;
        }}

        .translated-text {{
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            margin-bottom: 8px;
        }}

        .original-text {{
            font-size: 13px;
            color: #666;
        }}

        .original-text summary {{
            cursor: pointer;
            color: #1d9bf0;
        }}

        .original-text p {{
            margin-top: 8px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .tweet-analysis {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }}

        .scores {{
            display: flex;
            gap: 24px;
            margin-bottom: 12px;
        }}

        .score {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .score-label {{
            font-size: 12px;
            color: #666;
            width: 60px;
        }}

        .score-bar {{
            flex: 1;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}

        .score-fill {{
            height: 100%;
            border-radius: 4px;
        }}

        .score-fill.relevance {{ background: linear-gradient(90deg, #667eea, #764ba2); }}
        .score-fill.potential {{ background: linear-gradient(90deg, #28a745, #20c997); }}

        .score-value {{
            font-size: 12px;
            font-weight: bold;
            color: #333;
            width: 35px;
        }}

        .reasoning, .reply-suggestion {{
            font-size: 14px;
            color: #555;
            line-height: 1.5;
            margin-top: 8px;
        }}

        .reply-suggestion {{
            background: #e7f3ff;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #1d9bf0;
        }}

        .tweet-actions {{
            display: flex;
            gap: 8px;
        }}

        .btn {{
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .btn-primary {{
            background: #1d9bf0;
            color: white;
        }}

        .btn-primary:hover {{
            background: #1a8cd8;
        }}

        footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            padding: 24px;
            font-size: 14px;
        }}

        footer a {{
            color: white;
        }}

        @media (max-width: 768px) {{
            .stats {{
                flex-wrap: wrap;
            }}
            .stat {{
                flex: 1;
                min-width: 100px;
            }}
            .scores {{
                flex-direction: column;
                gap: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <svg viewBox="0 0 24 24" fill="#1d9bf0">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                X热门帖子监控
            </h1>
            <div class="header-meta">
                <span>Sparticle 营销助手 - AI驱动的社交媒体机会发现</span>
                <span>更新时间：{last_updated.strftime('%Y-%m-%d %H:%M UTC')}</span>
            </div>
            <div class="stats">
                <div class="stat high">
                    <div class="stat-value">{len(high_priority)}</div>
                    <div class="stat-label">高优先级</div>
                </div>
                <div class="stat medium">
                    <div class="stat-value">{len(recommended)}</div>
                    <div class="stat-label">建议回复</div>
                </div>
                <div class="stat low">
                    <div class="stat-value">{len(optional)}</div>
                    <div class="stat-label">可选回复</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(analyzed_tweets)}</div>
                    <div class="stat-label">总计发现</div>
                </div>
            </div>
        </header>

        {tweet_section('🔥 高优先级 - 立即行动', high_priority, 'section-high')}
        {tweet_section('💡 建议回复', recommended, 'section-medium')}
        {tweet_section('📝 可选回复', optional, 'section-low')}

        <footer>
            <p>由 <a href="https://github.com/lirhcoder/x-trending-monitor">X Trending Monitor</a> 自动生成</p>
            <p>Powered by Google Gemini AI | 数据来源：X/Twitter</p>
        </footer>
    </div>
</body>
</html>"""

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")
    return output_path


def generate_json_data(analyzed_tweets: list[dict], output_path: str = "docs/data.json"):
    """Generate JSON data file for the dashboard."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    data = {
        'last_updated': datetime.utcnow().isoformat(),
        'total_tweets': len(analyzed_tweets),
        'tweets': analyzed_tweets
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Data JSON generated: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with sample data
    sample_tweets = [
        {
            'tweet_id': '123',
            'original_text': 'Just tested the new AI meeting transcription tool. Game changer!',
            'translated_text': '刚测试了新的AI会议转录工具，太棒了！',
            'author_username': 'techguru',
            'engagement': 5000,
            'url': 'https://x.com/techguru/status/123',
            'relevance_score': 9,
            'engagement_potential': 8,
            'recommended_action': '高优先级回复',
            'reasoning': '讨论AI会议转录，与GBase核心功能高度匹配',
            'suggested_reply_angle': '可以介绍GBase的会议议事录功能',
            'priority_rank': 1
        },
        {
            'tweet_id': '456',
            'original_text': 'Looking for enterprise chatbot solutions',
            'translated_text': '寻找企业级聊天机器人解决方案',
            'author_username': 'cto_startup',
            'engagement': 800,
            'url': 'https://x.com/cto_startup/status/456',
            'relevance_score': 8,
            'engagement_potential': 7,
            'recommended_action': '建议回复',
            'reasoning': '明确需求与GBase Support匹配',
            'suggested_reply_angle': '推荐GBase Support的RAG功能',
            'priority_rank': 2
        }
    ]

    generate_dashboard_html(sample_tweets, 'test_dashboard.html')
