#!/usr/bin/env python3
"""
AI Analyzer for X/Twitter Posts
Uses Google Gemini to analyze posts, translate content, and recommend engagement priorities.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional
import google.generativeai as genai


# Sparticle company context for AI analysis
COMPANY_CONTEXT = """
Sparticle是一家日本AI公司，主要产品和服务包括：

1. **GBase** - 企业AI知识Hub
   - 会议议事录自动生成
   - 深度检索（跨文档AI搜索）
   - AI Agent自动化（资料生成、幻灯片创建）
   - 知识管理

2. **GBase Support** - 企业AI入口
   - AI Chatbot（自有数据构建）
   - 实时语音通话（AI自动应答）
   - RAG知识检索

3. **GBase GTM** - 商机匹配平台
   - 企业信息数据库
   - 自动外展营销
   - 潜在客户发现

4. **GBase OnPrem** - 本地部署AI硬件
   - 私有化部署
   - 安全合规

5. **Felo Subtitles** - AI实时翻译
   - 多语言实时字幕
   - 会议转录
   - 20+语言支持

核心技术：RAG、多语言处理、实时语音、LLM集成
目标客户：大型企业、政府机关、建筑/医疗/零售/金融/制造行业
"""


@dataclass
class AnalyzedTweet:
    """Tweet with AI analysis results."""
    tweet_id: str
    original_text: str
    translated_text: str
    author_username: str
    engagement: int
    url: str

    # AI Analysis
    relevance_score: int  # 1-10, how relevant to Sparticle
    engagement_potential: int  # 1-10, potential for meaningful engagement
    recommended_action: str  # AI suggested action
    reasoning: str  # Why this score
    suggested_reply_angle: str  # How to approach a reply
    priority_rank: int  # Final ranking

    def to_dict(self) -> dict:
        return {
            'tweet_id': self.tweet_id,
            'original_text': self.original_text,
            'translated_text': self.translated_text,
            'author_username': self.author_username,
            'engagement': self.engagement,
            'url': self.url,
            'relevance_score': self.relevance_score,
            'engagement_potential': self.engagement_potential,
            'recommended_action': self.recommended_action,
            'reasoning': self.reasoning,
            'suggested_reply_angle': self.suggested_reply_angle,
            'priority_rank': self.priority_rank
        }


class GeminiAnalyzer:
    """Analyze tweets using Google Gemini API."""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash or fall back to gemini-pro
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            except Exception:
                self.model = genai.GenerativeModel('gemini-pro')

    def analyze_tweets(self, tweets: list[dict]) -> list[AnalyzedTweet]:
        """Analyze a batch of tweets and return ranked recommendations."""
        if not tweets:
            return []

        # Prepare tweets for analysis
        tweets_text = "\n\n".join([
            f"[Tweet {i+1}]\n"
            f"Author: @{t.get('author_username', 'unknown')}\n"
            f"Engagement: {t.get('total_engagement', 0):,}\n"
            f"URL: {t.get('url', '')}\n"
            f"Text: {t.get('text', '')[:500]}"
            for i, t in enumerate(tweets[:20])  # Limit to 20 tweets per batch
        ])

        prompt = f"""你是Sparticle公司的社交媒体营销专家。分析以下X/Twitter帖子，判断哪些最值得互动以推广公司产品。

{COMPANY_CONTEXT}

---

以下是待分析的帖子：

{tweets_text}

---

请为每条帖子提供分析，输出JSON数组格式：

```json
[
  {{
    "tweet_index": 1,
    "translated_text": "帖子的中文翻译",
    "relevance_score": 8,
    "engagement_potential": 7,
    "recommended_action": "高优先级回复",
    "reasoning": "这条帖子讨论企业AI应用，与GBase产品高度相关...",
    "suggested_reply_angle": "可以分享GBase在会议记录自动化方面的案例..."
  }}
]
```

评分标准：
- relevance_score (1-10): 与Sparticle产品/服务的相关程度
- engagement_potential (1-10): 回复后获得曝光的潜力（考虑作者影响力、话题热度、讨论氛围）

recommended_action 选项：
- "高优先级回复" - 非常值得立即互动
- "建议回复" - 值得花时间互动
- "可选回复" - 有一定价值但非必须
- "仅观察" - 相关性低或不适合商业互动

只输出JSON数组，不要其他内容。"""

        try:
            print(f"Sending {len(tweets)} tweets to Gemini for analysis...")
            response = self.model.generate_content(prompt)

            # Check for blocked response
            if not response.text:
                print(f"Gemini returned empty response. Candidates: {response.candidates}")
                raise ValueError("Empty response from Gemini")

            response_text = response.text.strip()
            print(f"Gemini response length: {len(response_text)} chars")

            # Extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]

            response_text = response_text.strip()
            print(f"Extracted JSON length: {len(response_text)} chars")

            analyses = json.loads(response_text)
            print(f"Parsed {len(analyses)} tweet analyses")

            # Build analyzed tweets
            analyzed = []
            for analysis in analyses:
                idx = analysis.get('tweet_index', 1) - 1
                if idx < 0 or idx >= len(tweets):
                    continue

                tweet = tweets[idx]
                analyzed.append(AnalyzedTweet(
                    tweet_id=tweet.get('id', ''),
                    original_text=tweet.get('text', ''),
                    translated_text=analysis.get('translated_text', ''),
                    author_username=tweet.get('author_username', 'unknown'),
                    engagement=tweet.get('total_engagement', 0),
                    url=tweet.get('url', ''),
                    relevance_score=analysis.get('relevance_score', 0),
                    engagement_potential=analysis.get('engagement_potential', 0),
                    recommended_action=analysis.get('recommended_action', '仅观察'),
                    reasoning=analysis.get('reasoning', ''),
                    suggested_reply_angle=analysis.get('suggested_reply_angle', ''),
                    priority_rank=0  # Will be set after sorting
                ))

            # Sort by combined score and assign ranks
            analyzed.sort(
                key=lambda x: (x.relevance_score * 0.6 + x.engagement_potential * 0.4),
                reverse=True
            )

            for i, tweet in enumerate(analyzed):
                tweet.priority_rank = i + 1

            return analyzed

        except Exception as e:
            import traceback
            print(f"Error analyzing tweets with Gemini: {e}")
            print(f"Error type: {type(e).__name__}")
            traceback.print_exc()
            # Return tweets without AI analysis
            return [
                AnalyzedTweet(
                    tweet_id=t.get('id', ''),
                    original_text=t.get('text', ''),
                    translated_text='[翻译失败]',
                    author_username=t.get('author_username', 'unknown'),
                    engagement=t.get('total_engagement', 0),
                    url=t.get('url', ''),
                    relevance_score=0,
                    engagement_potential=0,
                    recommended_action='分析失败',
                    reasoning='AI分析出错',
                    suggested_reply_angle='',
                    priority_rank=i+1
                )
                for i, t in enumerate(tweets)
            ]


def create_analyzer() -> GeminiAnalyzer:
    """Create analyzer from environment variables."""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "No Google API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
        )
    return GeminiAnalyzer(api_key)


if __name__ == "__main__":
    # Test with sample data
    sample_tweets = [
        {
            'id': '123',
            'text': 'Just tested the new AI meeting transcription tool. Game changer for productivity!',
            'author_username': 'techguru',
            'total_engagement': 5000,
            'url': 'https://x.com/techguru/status/123'
        },
        {
            'id': '456',
            'text': 'Looking for enterprise RAG solutions. Anyone have recommendations?',
            'author_username': 'cto_startup',
            'total_engagement': 800,
            'url': 'https://x.com/cto_startup/status/456'
        }
    ]

    analyzer = create_analyzer()
    results = analyzer.analyze_tweets(sample_tweets)

    for r in results:
        print(f"\n#{r.priority_rank} @{r.author_username}")
        print(f"  Relevance: {r.relevance_score}/10")
        print(f"  Potential: {r.engagement_potential}/10")
        print(f"  Action: {r.recommended_action}")
        print(f"  翻译: {r.translated_text[:100]}...")
