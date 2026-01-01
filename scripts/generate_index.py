#!/usr/bin/env python3
"""
Generate index page with links to all historical dashboards.
"""

import os
import json
from datetime import datetime
from pathlib import Path


def generate_index():
    """Generate index.html with links to current and historical dashboards."""

    docs_dir = Path("docs")
    history_dir = docs_dir / "history"

    # Collect all historical dashboards
    history_data = []

    if history_dir.exists():
        for date_dir in sorted(history_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                date_str = date_dir.name
                dashboards = []

                for f in sorted(date_dir.glob("dashboard_*.html"), reverse=True):
                    # Extract timestamp from filename: dashboard_20260101_1200.html
                    try:
                        ts_str = f.stem.replace("dashboard_", "")
                        ts = datetime.strptime(ts_str, "%Y%m%d_%H%M")
                        jst_hour = (ts.hour + 9) % 24  # Convert UTC to JST

                        # Load data.json to get stats
                        data_file = f.with_name(f.stem.replace("dashboard_", "data_") + ".json")
                        stats = {"total": 0, "high_priority": 0}
                        if data_file.exists():
                            try:
                                with open(data_file, 'r', encoding='utf-8') as df:
                                    data = json.load(df)
                                    stats["total"] = data.get("total_tweets", 0)
                                    tweets = data.get("tweets", [])
                                    stats["high_priority"] = len([t for t in tweets if t.get("recommended_action") == "高优先级回复"])
                            except:
                                pass

                        dashboards.append({
                            "filename": f.name,
                            "path": f"history/{date_str}/{f.name}",
                            "time_utc": ts.strftime("%H:%M UTC"),
                            "time_jst": f"{jst_hour:02d}:00 JST",
                            "total": stats["total"],
                            "high_priority": stats["high_priority"]
                        })
                    except:
                        continue

                if dashboards:
                    history_data.append({
                        "date": date_str,
                        "dashboards": dashboards
                    })

    # Generate HTML
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
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

        .subtitle {{
            color: #666;
            font-size: 14px;
        }}

        .current-dashboard {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}

        .current-dashboard h2 {{
            color: #333;
            font-size: 18px;
            margin-bottom: 12px;
        }}

        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background: #1d9bf0;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: background 0.2s;
        }}

        .btn:hover {{
            background: #1a8cd8;
        }}

        .btn-large {{
            padding: 16px 32px;
            font-size: 16px;
        }}

        .history-section {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}

        .history-section h3 {{
            color: #333;
            font-size: 16px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }}

        .history-list {{
            display: grid;
            gap: 8px;
        }}

        .history-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            transition: background 0.2s;
        }}

        .history-item:hover {{
            background: #e9ecef;
        }}

        .history-time {{
            font-weight: 500;
        }}

        .history-stats {{
            display: flex;
            gap: 16px;
            font-size: 13px;
            color: #666;
        }}

        .stat-high {{
            color: #dc3545;
            font-weight: 500;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #666;
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
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="#1d9bf0">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                X热门帖子监控
            </h1>
            <p class="subtitle">Sparticle 营销助手 - AI驱动的社交媒体机会发现</p>
        </header>

        <div class="current-dashboard">
            <h2>📊 最新Dashboard</h2>
            <a href="dashboard.html" class="btn btn-large">查看当前监控结果</a>
        </div>

        <h2 style="color: white; margin-bottom: 16px; padding-left: 8px;">📁 历史记录</h2>
"""

    if history_data:
        for day in history_data:
            html += f"""
        <div class="history-section">
            <h3>📅 {day['date']}</h3>
            <div class="history-list">
"""
            for db in day['dashboards']:
                high_priority_badge = f'<span class="stat-high">🔥 {db["high_priority"]} 高优先</span>' if db["high_priority"] > 0 else ''
                html += f"""
                <a href="{db['path']}" class="history-item">
                    <span class="history-time">{db['time_jst']}</span>
                    <span class="history-stats">
                        <span>{db['total']} 条帖子</span>
                        {high_priority_badge}
                    </span>
                </a>
"""
            html += """
            </div>
        </div>
"""
    else:
        html += """
        <div class="history-section">
            <div class="empty-state">
                <p>暂无历史记录</p>
                <p style="font-size: 13px; margin-top: 8px;">监控运行后将自动保存历史数据</p>
            </div>
        </div>
"""

    html += """
        <footer>
            <p>由 <a href="https://github.com/lirhcoder/x-trending-monitor">X Trending Monitor</a> 自动生成</p>
            <p>每小时自动更新（日本时间 9:00-21:00）</p>
        </footer>
    </div>
</body>
</html>"""

    # Write index.html
    index_path = docs_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated index.html with {len(history_data)} days of history")


if __name__ == "__main__":
    generate_index()
