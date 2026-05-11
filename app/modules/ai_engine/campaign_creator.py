"""
AI 广告系列创建模块
给定落地页内容，生成完整的 Google Ads 搜索广告结构 JSON
"""
import json
import httpx
from app.core.config import settings

CAMPAIGN_CREATION_PROMPT = """You are an expert Google Ads campaign architect.
Given a landing page's content and business context, generate a complete Google Ads search campaign structure.

Output ONLY valid JSON matching this exact schema — no markdown, no explanation:
{
  "campaign_name": "string (max 128 chars, reflects product/service)",
  "daily_budget_usd": number,
  "bidding_strategy": "MANUAL_CPC",
  "ad_groups": [
    {
      "name": "string (ad group theme, max 255 chars)",
      "cpc_bid_usd": number,
      "keywords": [
        {"text": "string (max 80 chars)", "match_type": "PHRASE"}
      ],
      "negative_keywords": [
        {"text": "string", "match_type": "BROAD"}
      ],
      "headlines": ["string (MUST be max 30 chars each)"],
      "descriptions": ["string (MUST be max 90 chars each)"]
    }
  ]
}

Rules:
- Generate 2–4 ad groups, each focused on a distinct keyword theme from the landing page
- 5–10 keywords per ad group, prefer PHRASE and EXACT match types
- 3–8 broad negative keywords per ad group to exclude irrelevant traffic
- 8–10 headlines per ad group — max 30 chars each, no duplicate phrases across headlines
- 3–4 descriptions per ad group — max 90 chars each, specific and compelling
- Base ALL content on the actual landing page content provided; never invent facts
- Use the same language as the landing page content
- Headlines must not contain exclamation marks
"""


async def generate_campaign_plan(context: dict) -> dict:
    if settings.AI_PROVIDER == "gemini":
        return await _call_gemini(context)
    return await _call_openai(context)


async def _call_gemini(context: dict) -> dict:
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": CAMPAIGN_CREATION_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


async def _call_openai(context: dict) -> dict:
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": CAMPAIGN_CREATION_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])
