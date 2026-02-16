# CivicPulse

AI-powered infrastructure issue reporting platform that allows citizens to instantly report infrastructure issues with a photo and GPS pin.

## Features

- **Photo-Based Reporting**: Submit reports with photos; GPS is auto-extracted from EXIF data
- **AI Vision Analysis**: Automatic categorization and severity scoring via OpenAI Vision API
- **Duplicate Detection**: Haversine spatial search detects nearby reports within 50 meters
- **Interactive Heat Map**: Color-coded severity markers with clustering on Leaflet maps
- **Admin Dashboard**: Status management, category overrides, severity adjustments, audit logs
- **Leaderboard**: Top reporters ranked by submission count with opt-out privacy
- **Offline Mode**: PWA with IndexedDB draft storage and auto-upload on reconnection
- **Real-Time Updates**: WebSocket broadcasts for new reports and status changes
- **Role-Based Access**: JWT authentication with user/admin role separation

## Project Structure

```
civic-pulse/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST & WebSocket endpoints
│   │   ├── core/         # Auth, database, config
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── services/     # Business logic services
│   ├── tests/            # Backend tests (162+)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── context/      # Auth & Report contexts
│   │   ├── hooks/        # Custom hooks
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript interfaces
│   │   └── utils/        # EXIF, offline utilities
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml    # Docker Compose for local dev
└── .env.example          # Environment variable template
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or SQLite for development)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cp .env.example .env
# Edit .env with your settings
docker compose up --build
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./civicpulse.db` |
| `SECRET_KEY` | JWT signing secret | (required) |
| `OPENAI_API_KEY` | OpenAI API key for Vision | (optional, fallback to defaults) |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `RATE_LIMIT` | API rate limit | `100/minute` |
| `VITE_API_URL` | Backend API URL for frontend | `http://localhost:8000` |

## API Documentation

Interactive API docs available at `http://localhost:8000/docs` (Swagger UI).

### Key Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login, get JWT | No |
| GET | `/api/auth/me` | Current user profile | Yes |
| POST | `/api/reports/` | Submit report with photo | Yes |
| GET | `/api/reports/` | List reports with filters | Yes |
| GET | `/api/reports/my` | User's own reports | Yes |
| POST | `/api/reports/{id}/upvote` | Upvote a report | Yes |
| POST | `/api/admin/reports/{id}/status` | Update status | Admin |
| PATCH | `/api/admin/reports/{id}/category` | Override category | Admin |
| PATCH | `/api/admin/reports/{id}/severity` | Adjust severity | Admin |
| POST | `/api/admin/reports/{id}/notes` | Add internal note | Admin |
| GET | `/api/leaderboard/` | Top reporters | No |
| WS | `/ws` | Real-time updates | No |

## Testing

### Backend (162+ tests)

```bash
cd backend
python -m pytest tests/ -q
```

### Frontend (19 tests)

```bash
cd frontend
npm test
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, python-jose (JWT), bcrypt, OpenAI
- **Frontend**: React 18, TypeScript, Vite, Leaflet, Tailwind CSS
- **Database**: PostgreSQL (production), SQLite (development/testing)
- **Offline**: IndexedDB, Workbox PWA, Service Worker
- **Real-Time**: FastAPI WebSocket
- **Testing**: pytest, Hypothesis (property-based), Jest, React Testing Library

## Team

- **Brighton Dube** (Team Lead)
- **Tadiwanashe Divine Mphame**
- **Emmanuel Chidiebere Nzeh**
- **Valeriia Lebedieva**
