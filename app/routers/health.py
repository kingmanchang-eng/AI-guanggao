from fastapi import APIRouter
from app.db.supabase_client import get_client

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/db")
async def health_db():
    try:
        db = get_client()
        db.table("websites").select("id").limit(1).execute()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
