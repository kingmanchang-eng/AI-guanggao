import json
import httpx
from app.core.config import settings
from app.db.supabase_client import get_client

ALLOWED_ACTIONS = {
    "CREATE_CAMPAIGN_BUDGET", "UPDATE_CAMPAIGN_BUDGET",
    "CREATE_SEARCH_CAMPAIGN", "UPDATE_CAMPAIGN_STATUS",
    "CREATE_AD_GROUP", "UPDATE_AD_GROUP_STATUS",
    "ADD_KEYWORD", "PAUSE_KEYWORD", "ADD_NEGATIVE_KEYWORD",
    "CREATE_RESPONSIVE_SEARCH_AD", "PAUSE_AD",
    "UPDATE_LOCATION_TARGETING", "UPDATE_LANGUAGE_TARGETING",
}

SYSTEM_PROMPT = """You are an expert Google Ads optimizer. Given a website's ad performance data,
generate a structured JSON optimization plan.

Rules:
- Only output valid JSON, no markdown, no explanation text.
- Only use allowed action_types from the provided whitelist.
- Every action must include: action_type, campaign_id, reason, confidence (0-1), risk_level (low/medium/high).
- For CREATE_RESPONSIVE_SEARCH_AD: include final_url, headlines (list), descriptions (list).
- For keyword actions: include keyword_text and match_type.
- final_url must only use domains from allowed_domains.
- Never suggest deleting campaigns or ad groups.
- Never suggest modifying conversion goals or billing.
"""


async def run_optimization_plan(website_id: str):
    db = get_client()

    binding = (
        db.table("website_ads_account_bindings")
        .select("*, websites(*)")
        .eq("website_id", website_id)
        .eq("ai_autopilot_enabled", True)
        .eq("status", "active")
        .eq("safety_paused", False)
        .limit(1)
        .execute()
    )
    if not binding.data:
        return

    b = binding.data[0]
    customer_id = b["customer_id"]
    manager_account_id = b["manager_account_id"]
    website = b["websites"]

    context = {
        "website_id": website_id,
        "domain": website["domain"],
        "customer_id": customer_id,
        "manager_account_id": manager_account_id,
        "allowed_domains": b.get("allowed_domains") or [website["domain"]],
        "task_type": "daily_optimization",
        "allowed_action_types": list(ALLOWED_ACTIONS),
        "account_limits": {
            "daily_budget_cap": b.get("daily_budget_cap"),
            "single_budget_change_rate_cap": b.get("single_budget_change_rate_cap", 0.15),
            "max_actions_per_day": b.get("max_actions_per_day", 50),
        },
    }

    perf_data = _fetch_recent_performance(db, website_id, customer_id)
    context["performance_summary"] = perf_data

    output_json = await _call_ai(context)
    if not output_json:
        return

    plan = (
        db.table("ai_plans")
        .insert({
            "website_id": website_id,
            "manager_account_id": manager_account_id,
            "customer_id": customer_id,
            "plan_type": "DAILY_OPTIMIZATION",
            "input_summary": context,
            "output_json": output_json,
            "status": "created",
        })
        .execute()
    )
    plan_id = plan.data[0]["id"]

    actions = output_json.get("actions", [])
    for action in actions:
        if action.get("action_type") not in ALLOWED_ACTIONS:
            continue
        db.table("ai_actions").insert({
            "plan_id": plan_id,
            "website_id": website_id,
            "manager_account_id": manager_account_id,
            "customer_id": customer_id,
            "campaign_id": action.get("campaign_id"),
            "ad_group_id": action.get("ad_group_id"),
            "action_type": action["action_type"],
            "payload_json": action,
            "reason": action.get("reason"),
            "confidence": action.get("confidence"),
            "risk_level": action.get("risk_level"),
            "status": "pending",
        }).execute()


def _fetch_recent_performance(db, website_id: str, customer_id: str) -> dict:
    campaigns = (
        db.table("campaign_snapshots")
        .select("campaign_id, campaign_name, date, metrics_json")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .order("date", desc=True)
        .limit(90)
        .execute()
    )
    keywords = (
        db.table("keyword_snapshots")
        .select("keyword_text, match_type, date, metrics_json")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .order("date", desc=True)
        .limit(200)
        .execute()
    )
    search_terms = (
        db.table("search_term_snapshots")
        .select("search_term, metrics_json")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .limit(100)
        .execute()
    )
    return {
        "campaigns": campaigns.data,
        "keywords": keywords.data,
        "search_terms": search_terms.data,
    }


async def _call_ai(context: dict) -> dict | None:
    if settings.AI_PROVIDER == "openai":
        return await _call_openai(context)
    return None


async def _call_openai(context: dict) -> dict | None:
    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
