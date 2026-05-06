from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_client

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class ManagerAccountCreate(BaseModel):
    login_customer_id: str
    manager_name: Optional[str] = None
    oauth_user_email: Optional[str] = None


class AdsAccountCreate(BaseModel):
    manager_account_id: str
    customer_id: str
    account_name: Optional[str] = None
    currency_code: Optional[str] = None
    time_zone: Optional[str] = None


class BindingCreate(BaseModel):
    website_id: str
    manager_account_id: str
    ads_account_id: str
    customer_id: str
    daily_budget_cap: Optional[float] = None
    allowed_campaigns: list[str] = []
    blocked_campaigns: list[str] = []
    allowed_countries: list[str] = []
    allowed_languages: list[str] = []


@router.get("/managers")
async def list_managers():
    db = get_client()
    result = db.table("manager_accounts").select("id, login_customer_id, manager_name, oauth_user_email, status").execute()
    return result.data


@router.post("/managers")
async def create_manager(payload: ManagerAccountCreate):
    db = get_client()
    result = db.table("manager_accounts").insert(payload.model_dump()).execute()
    return result.data[0]


@router.get("/ads")
async def list_ads_accounts():
    db = get_client()
    result = db.table("ads_accounts").select("*").execute()
    return result.data


@router.post("/ads")
async def create_ads_account(payload: AdsAccountCreate):
    db = get_client()
    result = db.table("ads_accounts").insert(payload.model_dump()).execute()
    return result.data[0]


@router.get("/bindings")
async def list_bindings():
    db = get_client()
    result = db.table("website_ads_account_bindings").select("*, websites(domain, name), ads_accounts(account_name, customer_id)").execute()
    return result.data


@router.post("/bindings")
async def create_binding(payload: BindingCreate):
    db = get_client()
    result = db.table("website_ads_account_bindings").insert(payload.model_dump()).execute()
    return result.data[0]


@router.patch("/bindings/{binding_id}/autopilot")
async def toggle_autopilot(binding_id: str, enabled: bool):
    db = get_client()
    db.table("website_ads_account_bindings").update({"ai_autopilot_enabled": enabled}).eq("id", binding_id).execute()
    return {"ok": True, "ai_autopilot_enabled": enabled}
