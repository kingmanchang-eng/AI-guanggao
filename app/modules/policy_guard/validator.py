from app.db.supabase_client import get_client


FORBIDDEN_ACTIONS = {
    "DELETE_CAMPAIGN", "DELETE_AD_GROUP",
    "MODIFY_CONVERSION_GOAL", "MODIFY_BILLING",
    "MODIFY_ACCOUNT_PERMISSIONS",
}

ALLOWED_ACTIONS = {
    "CREATE_CAMPAIGN_BUDGET", "UPDATE_CAMPAIGN_BUDGET",
    "CREATE_SEARCH_CAMPAIGN", "UPDATE_CAMPAIGN_STATUS",
    "CREATE_AD_GROUP", "UPDATE_AD_GROUP_STATUS",
    "ADD_KEYWORD", "PAUSE_KEYWORD", "ADD_NEGATIVE_KEYWORD",
    "CREATE_RESPONSIVE_SEARCH_AD", "PAUSE_AD",
    "UPDATE_LOCATION_TARGETING", "UPDATE_LANGUAGE_TARGETING",
}


def validate_action(action: dict, binding: dict, website: dict) -> tuple[bool, str]:
    action_type = action.get("action_type", "")

    if action_type in FORBIDDEN_ACTIONS:
        return False, f"Action {action_type} is forbidden"

    if action_type not in ALLOWED_ACTIONS:
        return False, f"Action {action_type} is not in the whitelist"

    if action.get("website_id") and action["website_id"] != binding["website_id"]:
        return False, "website_id mismatch"

    if action.get("customer_id") and action["customer_id"] != binding["customer_id"]:
        return False, "customer_id mismatch"

    if action.get("manager_account_id") and action["manager_account_id"] != binding["manager_account_id"]:
        return False, "manager_account_id mismatch"

    payload = action.get("payload_json", action)
    final_url = payload.get("final_url", "")
    if final_url:
        allowed_domains = binding.get("allowed_domains") or [website.get("domain", "")]
        if not any(final_url.startswith(f"https://{d}") or final_url.startswith(f"http://{d}") for d in allowed_domains):
            return False, f"final_url domain not in allowed_domains: {final_url}"

    blocked = binding.get("blocked_campaigns") or []
    if action.get("campaign_id") in blocked:
        return False, f"Campaign {action.get('campaign_id')} is blocked"

    brand_terms = website.get("brand_terms") or []
    protected = website.get("protected_keywords") or []
    keyword_text = payload.get("keyword_text", "").lower()
    if action_type in ("ADD_NEGATIVE_KEYWORD", "PAUSE_KEYWORD") and keyword_text:
        for term in brand_terms + protected:
            if term.lower() in keyword_text:
                return False, f"Keyword '{keyword_text}' matches protected term '{term}'"

    return True, "ok"


def check_daily_limits(website_id: str, customer_id: str, max_actions: int) -> tuple[bool, str]:
    db = get_client()
    from datetime import date
    today = date.today().isoformat()
    result = (
        db.table("ai_actions")
        .select("id", count="exact")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .eq("status", "executed")
        .gte("executed_at", f"{today}T00:00:00")
        .execute()
    )
    executed_today = result.count or 0
    if executed_today >= max_actions:
        return False, f"Daily action limit reached: {executed_today}/{max_actions}"
    return True, "ok"
