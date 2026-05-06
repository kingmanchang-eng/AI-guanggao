from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.supabase_client import get_client
from app.modules.ai_engine.planner import run_optimization_plan
from app.modules.mutate_executor.executor import execute_pending_actions
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    scheduler.add_job(job_daily_optimize, CronTrigger(hour=3, minute=0), id="daily_optimize", replace_existing=True)
    scheduler.add_job(job_daily_execute, CronTrigger(hour=4, minute=0), id="daily_execute", replace_existing=True)
    scheduler.add_job(job_safety_check, CronTrigger(hour="*/1"), id="safety_check", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started")


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
