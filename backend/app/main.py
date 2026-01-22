from fastapi import FastAPI

app = FastAPI(title="CivicPulse API")


@app.get("/")
def read_root():
    return {"message": "Welcome to CivicPulse API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
