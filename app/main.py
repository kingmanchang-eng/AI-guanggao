from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers import health, websites, accounts, jobs, campaigns
from app.modules.scheduler.jobs import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENABLE_SCHEDULER:
        start_scheduler()
    yield


app = FastAPI(
    title="AI Google Ads Operator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_BASE_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip auth for health check and OPTIONS preflight
    if request.url.path == "/health/db" or request.method == "OPTIONS":
        return await call_next(request)
    # If API_KEY is configured, enforce it
    if settings.API_KEY:
        key = request.headers.get("X-API-Key", "")
        if key != settings.API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
    return await call_next(request)

app.include_router(health.router)
app.include_router(websites.router)
app.include_router(accounts.router)
app.include_router(jobs.router)
app.include_router(campaigns.router)

# api_key: enabled
