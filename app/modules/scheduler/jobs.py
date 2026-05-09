from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.supabase_client import get_client
from app.modules.ai_engine.planner import run_optimization_plan
from app.modules.mutate_executor.executor import execute_pending_actions
from app.modules.google_ads.sync import sync_website_data
from app.modules.google_ads.client import is_google_ads_configured
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    # 每天凌晨2点同步 Google Ads 数据
    scheduler.add_job(job_daily_sync, CronTrigger(hour=2, minute=0), id="daily_sync", replace_existing=True)
    # 每天凌晨3点生成 AI 优化计划
    scheduler.add_job(job_daily_optimize, CronTrigger(hour=3, minute=0), id="daily_optimize", replace_existing=True)
    # 每天凌晨4点执行 AI 动作
    scheduler.add_job(job_daily_execute, CronTrigger(hour=4, minute=0), id="daily_execute", replace_existing=True)
    # 每小时安全检查
    scheduler.add_job(job_safety_check, CronTrigger(hour="*/1"), id="safety_check", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started")


async def job_daily_sync():
    """每日同步 Google Ads 数据"""
    if not is_google_ads_configured():
        logger.info("Google Ads API 未配置，跳过数据同步")
        return
    db = get_client()
    bindings = (
        db.table("website_ads_account_bindings")
        .select("website_id, customer_id, manager_account_id")
        .eq("ai_autopilot_enabled", True)
        .eq("status", "active")
        .eq("safety_paused", False)
        .execute()
    )
    for b in bindings.data:
        try:
            manager = db.table("manager_accounts").select("login_customer_id").eq("id", b["manager_account_id"]).single().execute()
            login_cid = manager.data["login_customer_id"] if manager.data else ""
            sync_website_data(
                website_id=b["website_id"],
                customer_id=b["customer_id"],
                login_customer_id=login_cid,
                manager_account_id=b["manager_account_id"],
            )
        except Exception as e:
            logger.error(f"Sync failed for website {b['website_id']}: {e}")


async def job_daily_optimize():
    db = get_client()
    bindings = (
        db.table("website_ads_account_bindings")
        .select("website_id")
        .eq("ai_autopilot_enabled", True)
        .eq("status", "active")
        .eq("safety_paused", False)
        .execute()
    )
    for b in bindings.data:
        try:
            await run_optimization_plan(b["website_id"])
        except Exception as e:
            logger.error(f"Optimize failed for website {b['website_id']}: {e}")


async def job_daily_execute():
    db = get_client()
    bindings = (
        db.table("website_ads_account_bindings")
        .select("website_id")
        .eq("ai_autopilot_enabled", True)
        .eq("status", "active")
        .eq("safety_paused", False)
        .execute()
    )
    for b in bindings.data:
        try:
            await execute_pending_actions(b["website_id"])
        except Exception as e:
            logger.error(f"Execute failed for website {b['website_id']}: {e}")


async def job_safety_check():
    db = get_client()
    result = (
        db.table("website_ads_account_bindings")
        .select("website_id, customer_id")
        .eq("safety_paused", True)
        .execute()
    )
    if result.data:
        logger.warning(f"{len(result.data)} sites currently safety-paused")
