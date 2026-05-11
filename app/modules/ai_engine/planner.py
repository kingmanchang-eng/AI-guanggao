import json
import httpx
from app.core.config import settings
from app.db.supabase_client import get_client

ALLOWED_ACTIONS = {
    "CREATE_CAMPAIGN_BUDGET", "UPDATE_CAMPAIGN_BUDGET",
    "CREATE_SEARCH_CAMPAIGN", "CREATE_CAMPAIGN", "UPDATE_CAMPAIGN_STATUS",
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


STRUCTURE_SYSTEM_PROMPT = """You are an expert Google Ads account architect. Given weekly performance data,
generate a structured JSON plan focused on account structure improvements.

Rules:
- Only output valid JSON, no markdown, no explanation text.
- Focus on structural actions: CREATE_CAMPAIGN_BUDGET, CREATE_CAMPAIGN, CREATE_AD_GROUP,
  UPDATE_LOCATION_TARGETING, UPDATE_LANGUAGE_TARGETING.
- Every action must include: action_type, reason, confidence (0-1), risk_level (low/medium/high).
- For CREATE_CAMPAIGN: include campaign_name, budget_resource_name or budget amount, bidding_strategy.
- For CREATE_AD_GROUP: include ad_group_name, campaign_id.
- For location/language targeting: include campaign_id, geo_target_ids or language_ids.
- final_url must only use domains from allowed_domains.
- Never suggest deleting campaigns or ad groups.
- Never suggest modifying conversion goals or billing.
"""


async def run_structure_optimization_plan(website_id: str):
    """每周结构优化：聚焦账户层级结构（新建Campaign/AdGroup/定向调整）"""
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

    structure_action_types = [
        "CREATE_CAMPAIGN_BUDGET", "CREATE_CAMPAIGN", "CREATE_AD_GROUP",
        "UPDATE_LOCATION_TARGETING", "UPDATE_LANGUAGE_TARGETING",
    ]

    context = {
        "website_id": website_id,
        "domain": website["domain"],
        "customer_id": customer_id,
        "manager_account_id": manager_account_id,
        "allowed_domains": b.get("allowed_domains") or [website["domain"]],
        "task_type": "weekly_structure_optimization",
        "allowed_action_types": structure_action_types,
        "account_limits": {
            "daily_budget_cap": b.get("daily_budget_cap"),
            "max_actions_per_week": b.get("max_actions_per_day", 50),
        },
    }

    perf_data = _fetch_recent_performance(db, website_id, customer_id)
    context["performance_summary"] = perf_data

    output_json = await _call_ai_with_prompt(context, STRUCTURE_SYSTEM_PROMPT)
    if not output_json:
        return

    plan = (
        db.table("ai_plans")
        .insert({
            "website_id": website_id,
            "manager_account_id": manager_account_id,
            "customer_id": customer_id,
            "plan_type": "WEEKLY_STRUCTURE",
            "input_summary": context,
            "output_json": output_json,
            "status": "created",
        })
        .execute()
    )
    plan_id = plan.data[0]["id"]

    actions = output_json.get("actions", [])
    for action in actions:
        if action.get("action_type") not in structure_action_types:
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


async def _call_ai_with_prompt(context: dict, system_prompt: str) -> dict | None:
    if settings.AI_PROVIDER == "gemini":
        return await _call_gemini_with_prompt(context, system_prompt)
    if settings.AI_PROVIDER == "openai":
        return await _call_openai_with_prompt(context, system_prompt)
    return None


async def _call_gemini_with_prompt(context: dict, system_prompt: str) -> dict | None:
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


async def _call_openai_with_prompt(context: dict, system_prompt: str) -> dict | None:
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])


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
    ad_groups = (
        db.table("ad_group_snapshots")
        .select("campaign_id, ad_group_id, ad_group_name, date, metrics_json")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .order("date", desc=True)
        .limit(200)
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
        "ad_groups": ad_groups.data,
        "keywords": keywords.data,
        "search_terms": search_terms.data,
    }


async def _call_ai(context: dict) -> dict | None:
    if settings.AI_PROVIDER == "gemini":
        return await _call_gemini(context)
    if settings.AI_PROVIDER == "openai":
        return await _call_openai(context)
    return None


async def _call_gemini(context: dict) -> dict | None:
    # Gemini OpenAI-compatible endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
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
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


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
