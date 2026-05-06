from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers import health, websites, accounts, jobs
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
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(websites.router)
app.include_router(accounts.router)
app.include_router(jobs.router)
