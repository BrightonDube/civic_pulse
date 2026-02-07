# CivicPulse

Infrastructure issue reporting platform with a FastAPI backend and React frontend.

## Project Structure

```
civic_pulse/
  backend/       FastAPI backend
  frontend/      React + TypeScript frontend
```

## Quick Start

Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

## Local URLs

- Backend API docs: http://localhost:8000/docs
- Frontend app: http://localhost:5173

## Database Migrations (Alembic)

From `backend/`:
```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply latest migrations
alembic upgrade head
```

Make sure `DATABASE_URL` in `backend/.env` points to your local database.

## Platform Features Added

- Structured API routes for health and issues
- Database model and Pydantic schemas for issues
- Service layer for issue creation and listing
- Frontend API client with environment config
- Navigation shell, error boundary, and basic styling

## Next Improvements

- Add authentication and role-based access
- Add issue status updates and admin workflows
