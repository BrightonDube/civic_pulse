from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.auth import router as auth_router
from app.api.reports import router as reports_router
from app.api.admin import router as admin_router
from app.api.leaderboard import router as leaderboard_router
from app.api.ws import router as ws_router
from app.api.analytics import router as analytics_router
from app.api.routes.config import router as config_router
from app.core.database import engine, Base
import app.models  # ensure all models are loaded
import os

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="CivicPulse API",
    description="AI-powered infrastructure issue reporting platform",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(leaderboard_router)
app.include_router(ws_router)
app.include_router(analytics_router)
app.include_router(config_router)

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Serve uploaded photos
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def read_root():
    return {"message": "Welcome to CivicPulse API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
