# CivicPulse

AI-powered infrastructure issue reporting platform that allows citizens to instantly report infrastructure issues with a photo and GPS pin.

## Project Structure

```
civic-pulse/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── alembic/     # Database migrations
│   └── tests/       # Backend tests
└── frontend/        # React TypeScript frontend
    └── src/         # Frontend source code
```

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Documentation

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:5173

---

## Brighton Dube's Favourite Quote

> "Progress is built on small acts done consistently — especially the ones no one asked you to do."
