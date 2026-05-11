"""
广告系列创建 API
POST /api/campaigns/preview  — 抓取落地页 + AI 生成方案预览，不创建任何资源
POST /api/campaigns/create   — 生成方案并直接在 Google Ads 创建完整广告结构
"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.db.supabase_client import get_client
from app.modules.landing_page.reader import fetch_landing_page
from app.modules.ai_engine.campaign_creator import generate_campaign_plan
from app.modules.google_ads.campaign_builder import build_campaign_from_plan
from app.modules.google_ads.client import is_google_ads_configured

logger = logging.getLogger(__name__)
router = APIRouter()


class CampaignRequest(BaseModel):
    website_id: str
    landing_page_url: str
    campaign_name: Optional[str] = None
    daily_budget_usd: Optional[float] = 50.0
    bidding_strategy: Optional[str] = "MANUAL_CPC"
    start_paused: Optional[bool] = True


def _get_binding(db, website_id: str):
    res = (
        db.table("website_ads_account_bindings")
        .select("*, websites(*)")
        .eq("website_id", website_id)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _build_context(req: CampaignRequest, b: dict, page_content: dict) -> dict:
    website = b["websites"]
    return {
        "task_type": "campaign_creation_from_landing_page",
        "website_id": req.website_id,
        "domain": website["domain"],
        "allowed_domains": b.get("allowed_domains") or [website["domain"]],
        "landing_page_url": req.landing_page_url,
        "landing_page_content": page_content,
        "campaign_config": {
            "campaign_name_hint": req.campaign_name or "",
            "daily_budget_usd": req.daily_budget_usd,
            "bidding_strategy": req.bidding_strategy,
        },
    }


def _apply_overrides(plan: dict, req: CampaignRequest) -> dict:
    if req.campaign_name:
        plan["campaign_name"] = req.campaign_name
    plan["daily_budget_usd"] = req.daily_budget_usd
    plan["bidding_strategy"] = req.bidding_strategy
    return plan


@router.post("/api/campaigns/preview")
async def preview_campaign(req: CampaignRequest):
    """抓取落地页内容 + AI 生成广告方案，返回预览（不创建任何 Google Ads 资源）"""
    db = get_client()
    b = _get_binding(db, req.website_id)
    if not b:
        return {"error": "找不到该网站的有效广告账号绑定"}

    try:
        page_content = await fetch_landing_page(req.landing_page_url)
    except Exception as e:
        return {"error": f"无法访问落地页: {e}"}

    try:
        plan = await generate_campaign_plan(_build_context(req, b, page_content))
    except Exception as e:
        logger.error(f"AI 生成计划失败: {e}")
        return {"error": f"AI 生成计划失败: {e}"}

    _apply_overrides(plan, req)

    return {
        "plan": plan,
        "page_content": {
            "title": page_content["title"],
            "meta_description": page_content["meta_description"],
            "headings": page_content["headings"],
        },
    }


@router.post("/api/campaigns/create")
async def create_campaign(req: CampaignRequest):
    """生成广告方案并直接在 Google Ads 创建完整广告结构"""
    if not is_google_ads_configured():
        return {"error": "Google Ads API 凭据未配置，请先在 Sealos 配置 Google Ads 环境变量"}

    db = get_client()
    b = _get_binding(db, req.website_id)
    if not b:
        return {"error": "找不到该网站的有效广告账号绑定"}

    customer_id = b["customer_id"]
    manager_account_id = b["manager_account_id"]
    mgr = (
        db.table("manager_accounts")
        .select("login_customer_id")
        .eq("id", manager_account_id)
        .single()
        .execute()
    )
    login_customer_id = mgr.data["login_customer_id"] if mgr.data else ""

    try:
        page_content = await fetch_landing_page(req.landing_page_url)
    except Exception as e:
        return {"error": f"无法访问落地页: {e}"}

    try:
        plan = await generate_campaign_plan(_build_context(req, b, page_content))
    except Exception as e:
        logger.error(f"AI 生成计划失败: {e}")
        return {"error": f"AI 生成计划失败: {e}"}

    _apply_overrides(plan, req)

    # 保存 AI 计划到数据库
    plan_record = (
        db.table("ai_plans")
        .insert({
            "website_id": req.website_id,
            "manager_account_id": manager_account_id,
            "customer_id": customer_id,
            "plan_type": "CAMPAIGN_CREATION",
            "input_summary": {"landing_page_url": req.landing_page_url, "page_title": page_content["title"]},
            "output_json": plan,
            "status": "executing",
        })
        .execute()
    )
    plan_id = plan_record.data[0]["id"]

    # 执行创建
    build_result = build_campaign_from_plan(
        plan=plan,
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        final_url=req.landing_page_url,
        start_paused=req.start_paused,
    )

    final_status = "completed" if not build_result["errors"] else "partial"
    db.table("ai_plans").update({"status": final_status}).eq("id", plan_id).execute()

    return {
        "plan_id": plan_id,
        "plan": plan,
        "result": build_result,
        "status": final_status,
    }
