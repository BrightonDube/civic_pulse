from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def read_root():
    return {"message": "Welcome to CivicPulse API"}


@router.get("/health")
def health_check():
    return {"status": "healthy"}
