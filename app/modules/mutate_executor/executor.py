from datetime import datetime, timezone
from app.db.supabase_client import get_client
from app.modules.policy_guard.validator import validate_action, check_daily_limits
from app.core.config import settings


async def execute_pending_actions(website_id: str):
    db = get_client()

    binding_res = (
        db.table("website_ads_account_bindings")
        .select("*, websites(*)")
        .eq("website_id", website_id)
        .eq("ai_autopilot_enabled", True)
        .eq("status", "active")
        .eq("safety_paused", False)
        .limit(1)
        .execute()
    )
    if not binding_res.data:
        return

    binding = binding_res.data[0]
    website = binding["websites"]
    customer_id = binding["customer_id"]
    max_actions = binding.get("max_actions_per_day", settings.DEFAULT_SITE_DAILY_ACTION_LIMIT)

    limit_ok, limit_msg = check_daily_limits(website_id, customer_id, max_actions)
    if not limit_ok:
        _log_safety_event(db, website_id, binding["manager_account_id"], customer_id, "DAILY_LIMIT_REACHED", limit_msg)
        return

    actions = (
        db.table("ai_actions")
        .select("*")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .eq("status", "pending")
        .order("created_at")
        .limit(max_actions)
        .execute()
    )

    for action in actions.data:
        ok, reason = validate_action(action, binding, website)
        if not ok:
            db.table("ai_actions").update({"status": "rejected"}).eq("id", action["id"]).execute()
            _write_mutate_log(db, action, None, False, reason, validate_only=False)
            continue

        is_validate_only = settings.ENABLE_VALIDATE_ONLY and not settings.ENABLE_PRODUCTION_MUTATE
        success, response, error = await _call_google_ads_mutate(action, binding)
        status = "executed" if success else "failed"
        db.table("ai_actions").update({
            "status": status,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", action["id"]).execute()
        _write_mutate_log(db, action, response, success, error, validate_only=is_validate_only)

        if not success:
            _increment_api_failure(db, website_id, binding["manager_account_id"], customer_id)


async def _call_google_ads_mutate(action: dict, binding: dict) -> tuple[bool, dict | None, str | None]:
    # validate_only 模式：跳过真实 API 调用，直接返回成功
    if settings.ENABLE_VALIDATE_ONLY and not settings.ENABLE_PRODUCTION_MUTATE:
        return True, {"validate_only": True}, None

    from app.modules.google_ads.client import is_google_ads_configured
    if not is_google_ads_configured():
        return False, None, "Google Ads API 凭据未配置"

    from app.modules.google_ads.mutate import execute_action
    return execute_action(action, binding)


def _write_mutate_log(db, action: dict, response: dict | None, success: bool, error: str | None, validate_only: bool = False):
    db.table("mutate_logs").insert({
        "action_id": action["id"],
        "website_id": action["website_id"],
        "manager_account_id": action["manager_account_id"],
        "customer_id": action["customer_id"],
        "request_json": action.get("payload_json"),
        "response_json": response,
        "success": success,
        "validate_only": validate_only,
        "error_message": error,
    }).execute()


def _log_safety_event(db, website_id: str, manager_account_id: str, customer_id: str, event_type: str, detail: str):
    db.table("safety_events").insert({
        "website_id": website_id,
        "manager_account_id": manager_account_id,
        "customer_id": customer_id,
        "event_type": event_type,
        "severity": "high",
        "detail_json": {"message": detail},
    }).execute()


def _increment_api_failure(db, website_id: str, manager_account_id: str, customer_id: str):
    result = (
        db.table("safety_events")
        .select("id", count="exact")
        .eq("website_id", website_id)
        .eq("customer_id", customer_id)
        .eq("event_type", "API_FAILURE")
        .eq("resolved", False)
        .execute()
    )
    failure_count = result.count or 0
    if failure_count >= 3:
        db.table("website_ads_account_bindings").update({"safety_paused": True}).eq("website_id", website_id).execute()
        _log_safety_event(db, website_id, manager_account_id, customer_id, "AUTO_PAUSED", "Paused after 3 consecutive API failures")
