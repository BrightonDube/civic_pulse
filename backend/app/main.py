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
from app.api.users import router as users_router
from app.api.leaderboard import router as leaderboard_router
from app.api.ws import router as ws_router
from app.api.analytics import router as analytics_router
from app.api.notifications import router as notifications_router
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
app.include_router(users_router)
app.include_router(leaderboard_router)
app.include_router(ws_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
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


@app.post("/seed")
def seed_database(seed_key: str):
    """Seed the database with test users. Requires SEED_KEY for security."""
    import os
    from app.core.database import SessionLocal
    from app.models.user import User
    
    expected_key = os.getenv("SEED_KEY", "civicpulse-seed-2024")
    if seed_key != expected_key:
        return JSONResponse(status_code=403, content={"error": "Invalid seed key"})
    
    db = SessionLocal()
    results = []
    
    try:
        users_to_create = [
            {"email": "admin@civicpulse.com", "password": "admin123", "phone": "+1234567890", "role": "admin"},
            {"email": "bizpilot16@gmail.com", "password": "testuser123", "phone": "+1987654321", "role": "user"},
            {"email": "testuser@civicpulse.com", "password": "testuser123", "phone": "+1122334455", "role": "user"},
        ]
        
        for user_data in users_to_create:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                results.append({"email": user_data["email"], "status": "exists", "role": existing.role})
            else:
                user = User(
                    email=user_data["email"],
                    phone=user_data["phone"],
                    role=user_data["role"],
                    email_verified=True
                )
                user.set_password(user_data["password"])
                db.add(user)
                db.commit()
                results.append({"email": user_data["email"], "status": "created", "role": user_data["role"]})
        
        return {"message": "Seeding complete", "users": results}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        db.close()
