from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_client

router = APIRouter(prefix="/api/websites", tags=["websites"])


class WebsiteCreate(BaseModel):
    domain: str
    name: Optional[str] = None
    business_type: Optional[str] = None
    allowed_domains: list[str] = []
    allowed_landing_pages: list[str] = []
    brand_terms: list[str] = []
    protected_keywords: list[str] = []


@router.get("")
async def list_websites():
    db = get_client()
    result = db.table("websites").select("*").eq("status", "active").execute()
    return result.data


@router.post("")
async def create_website(payload: WebsiteCreate):
    db = get_client()
    result = db.table("websites").insert(payload.model_dump()).execute()
    return result.data[0]


@router.get("/{website_id}")
async def get_website(website_id: str):
    db = get_client()
    result = db.table("websites").select("*").eq("id", website_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Website not found")
    return result.data


@router.delete("/{website_id}")
async def disable_website(website_id: str):
    db = get_client()
    db.table("websites").update({"status": "disabled"}).eq("id", website_id).execute()
    return {"ok": True}
