from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.issues import router as issues_router
from app.core.config import settings

app = FastAPI(
    title="CivicPulse API",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "Service health and readiness."},
        {"name": "Issues", "description": "Civic issue reporting and tracking."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(issues_router)
