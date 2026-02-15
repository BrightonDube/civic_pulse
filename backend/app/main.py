from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.reports import router as reports_router
from app.api.admin import router as admin_router

app = FastAPI(
    title="CivicPulse API",
    description="AI-powered infrastructure issue reporting platform",
    version="1.0.0",
)

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


@app.get("/")
def read_root():
    return {"message": "Welcome to CivicPulse API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
