from fastapi import APIRouter, BackgroundTasks
from app.db.supabase_client import get_client
from app.modules.ai_engine.planner import run_optimization_plan
from app.modules.mutate_executor.executor import execute_pending_actions

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/sync/{website_id}")
async def trigger_sync(website_id: str, background_tasks: BackgroundTasks):
    """Trigger a manual data sync for a specific website."""
    background_tasks.add_task(_sync_website, website_id)
    return {"ok": True, "message": f"Sync started for website {website_id}"}


@router.post("/optimize/{website_id}")
async def trigger_optimize(website_id: str, background_tasks: BackgroundTasks):
    """Trigger AI optimization plan generation for a specific website."""
    background_tasks.add_task(run_optimization_plan, website_id)
    return {"ok": True, "message": f"Optimization started for website {website_id}"}


@router.post("/execute/{website_id}")
async def trigger_execute(website_id: str, background_tasks: BackgroundTasks):
    """Execute pending AI actions for a specific website."""
    background_tasks.add_task(execute_pending_actions, website_id)
    return {"ok": True, "message": f"Execution started for website {website_id}"}


@router.get("/plans/{website_id}")
async def list_plans(website_id: str, limit: int = 20):
    db = get_client()
    result = (
        db.table("ai_plans")
        .select("*")
        .eq("website_id", website_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.get("/actions/{website_id}")
async def list_actions(website_id: str, status: str = None, limit: int = 50):
    db = get_client()
    q = db.table("ai_actions").select("*").eq("website_id", website_id)
    if status:
        q = q.eq("status", status)
    result = q.order("created_at", desc=True).limit(limit).execute()
    return result.data


@router.get("/logs/{website_id}")
async def list_mutate_logs(website_id: str, limit: int = 50):
    db = get_client()
    result = (
        db.table("mutate_logs")
        .select("*")
        .eq("website_id", website_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


async def _sync_website(website_id: str):
    """Placeholder for Google Ads data sync — implemented in google_ads module."""
    pass
