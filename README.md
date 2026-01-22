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


# CivicPulse Project Tasks

## Team Members
- **Brighton Dube** (Team Lead)
- **Tadiwanashe Divine Mphame**
- **Emmanuel Chidiebere Nzeh**
- **Valeriia Lebedieva**

---

## Phase 1: Project Setup & Infrastructure (Week 1)

### Brighton Dube - Project Infrastructure & Database
- [ ] Set up project repository structure (backend/frontend folders)
- [ ] Initialize Python virtual environment and install dependencies (FastAPI, SQLAlchemy, Alembic, pytest, hypothesis)
- [ ] Set up PostgreSQL database with PostGIS extension
- [ ] Create initial database migrations (User, Report, Upvote, StatusHistory, AdminNote tables)
- [ ] Configure environment variables and .env files
- [ ] Set up CI/CD pipeline basics
- [ ] Create project documentation structure

### Tadiwanashe Divine Mphame - Frontend Setup
- [ ] Initialize React TypeScript project with Vite
- [ ] Set up project structure (components, services, hooks, utils)
- [ ] Install and configure dependencies (React, TypeScript, Leaflet.js, Workbox)
- [ ] Configure ESLint and Prettier for code quality
- [ ] Set up Jest and React Testing Library
- [ ] Create basic routing structure
- [ ] Set up PWA configuration with Workbox

### Emmanuel Chidiebere Nzeh - Backend Authentication
- [ ] Create User model with SQLAlchemy (email, password_hash, phone, role)
- [ ] Implement password hashing with bcrypt
- [ ] Create AuthService with registration and login methods
- [ ] Implement JWT token generation and validation
- [ ] Create authentication middleware for protected routes
- [ ] Implement role-based access control (RBAC)
- [ ] Write unit tests for authentication flow

### Valeriia Lebedieva - API Design & Documentation
- [ ] Design REST API endpoints structure
- [ ] Create Pydantic models for request/response validation
- [ ] Set up FastAPI application with CORS configuration
- [ ] Configure OpenAPI/Swagger documentation
- [ ] Create API client service for frontend
- [ ] Document API authentication flow
- [ ] Set up API error handling structure

---

## Phase 2: Core Report Functionality (Week 2-3)

### Brighton Dube - Report Service & Database
- [ ] Create Report model with PostGIS POINT for GPS coordinates
- [ ] Create spatial index on location column
- [ ] Implement ReportService with create_report method
- [ ] Implement photo upload handling and storage
- [ ] Create API endpoints for report submission and retrieval
- [ ] Write property tests for report data persistence
- [ ] Implement database constraint enforcement

### Tadiwanashe Divine Mphame - Report Submission UI
- [ ] Create photo capture/upload component
- [ ] Implement GPS extraction from EXIF metadata
- [ ] Integrate browser geolocation API for GPS fallback
- [ ] Create map component with Leaflet.js
- [ ] Build location preview with pin placement
- [ ] Create report submission form
- [ ] Implement form validation and error handling
- [ ] Write unit tests for report submission flow

### Emmanuel Chidiebere Nzeh - AI Integration
- [ ] Implement AIService with OpenAI Vision API integration
- [ ] Create API client for OpenAI Vision
- [ ] Implement response parsing for category and severity
- [ ] Add error handling and fallback logic (default: "Other", severity 5)
- [ ] Integrate AI analysis into report creation flow
- [ ] Implement retry logic with exponential backoff
- [ ] Write property tests for AI response parsing
- [ ] Write unit tests for AI service error handling

### Valeriia Lebedieva - Duplicate Detection
- [ ] Create DuplicateDetectionService with PostGIS spatial queries
- [ ] Implement ST_DWithin for 50-meter radius search
- [ ] Create Upvote model with unique constraint
- [ ] Implement upvoting logic with idempotency
- [ ] Integrate duplicate detection into report submission
- [ ] Create API endpoints for upvoting
- [ ] Write property tests for spatial search and duplicate detection
- [ ] Write unit tests for upvote functionality

---

## Phase 3: Admin Dashboard & Status Tracking (Week 4)

### Brighton Dube - Status Tracking & Notifications
- [ ] Create StatusHistory model for audit logging
- [ ] Implement status update functionality
- [ ] Create NotificationService with email integration (SMTP)
- [ ] Integrate Twilio for SMS notifications
- [ ] Implement notification queue for batch processing
- [ ] Trigger notifications on status changes
- [ ] Write property tests for status history and notifications
- [ ] Handle notification failures with retry queue

### Tadiwanashe Divine Mphame - Heat Map Dashboard
- [ ] Create admin dashboard layout and navigation
- [ ] Implement interactive map with Leaflet.js/Mapbox
- [ ] Display report markers with severity-based color coding
- [ ] Implement marker clustering for nearby reports
- [ ] Create report filtering controls (category, status, date)
- [ ] Build report detail modal with photo and metadata
- [ ] Add real-time updates (WebSocket or polling)
- [ ] Write unit tests for map components

### Emmanuel Chidiebere Nzeh - Admin Service
- [ ] Create AdminService with report management methods
- [ ] Implement status update endpoint for admins
- [ ] Create AdminNote model and add note functionality
- [ ] Implement category override capability
- [ ] Implement severity adjustment capability
- [ ] Create audit logging for all admin actions
- [ ] Implement report archival for fixed reports
- [ ] Write property tests for admin operations

### Valeriia Lebedieva - Report Filtering & API
- [ ] Create API endpoint for retrieving reports with filters
- [ ] Implement filtering logic (category, status, date, bounds)
- [ ] Implement PostGIS bounding box queries
- [ ] Create report clustering algorithm
- [ ] Add severity-based color coding to API response
- [ ] Optimize spatial queries for performance
- [ ] Write property tests for report filtering
- [ ] Write unit tests for clustering logic

---

## Phase 4: Offline Mode & Leaderboard (Week 5)

### Brighton Dube - Leaderboard Backend
- [ ] Add report_count and leaderboard_opt_out fields to User model
- [ ] Implement report count tracking (increment on creation)
- [ ] Create leaderboard API endpoint with geographic filtering
- [ ] Implement leaderboard ranking logic (top 10 users)
- [ ] Exclude opted-out users from leaderboard
- [ ] Optimize leaderboard queries for performance
- [ ] Write property tests for leaderboard functionality
- [ ] Write unit tests for report count accuracy

### Tadiwanashe Divine Mphame - Offline Mode & PWA
- [ ] Configure Workbox service worker for PWA
- [ ] Implement IndexedDB storage for offline drafts
- [ ] Create offline draft creation functionality
- [ ] Implement connectivity detection (online/offline events)
- [ ] Display offline mode indicator in UI
- [ ] Implement auto-upload of drafts when online
- [ ] Add retry logic with exponential backoff
- [ ] Write property tests for offline mode
- [ ] Test PWA installation and offline functionality

### Emmanuel Chidiebere Nzeh - User Dashboard & Leaderboard UI
- [ ] Create user dashboard showing user's reports
- [ ] Display report status and upvote count
- [ ] Implement user report filtering
- [ ] Create leaderboard component
- [ ] Display top 10 users with rank and report count
- [ ] Add geographic filter dropdown for leaderboard
- [ ] Create user settings page with leaderboard opt-out toggle
- [ ] Write unit tests for dashboard components

### Valeriia Lebedieva - API Validation & Rate Limiting
- [ ] Add Pydantic models for all API request validation
- [ ] Implement field validation (required fields, types, ranges)
- [ ] Add rate limiting middleware (100 requests/minute)
- [ ] Ensure consistent HTTP status codes across endpoints
- [ ] Create error handlers for common exceptions
- [ ] Write property tests for API validation
- [ ] Write property tests for rate limiting
- [ ] Document all API error responses

---

## Phase 5: Testing & Integration (Week 6)

### Brighton Dube - Backend Testing & Integration
- [ ] Run full backend test suite (unit + property tests)
- [ ] Verify all property-based tests pass (39 properties)
- [ ] Test API endpoints with Postman/Insomnia
- [ ] Perform integration testing with real database
- [ ] Test with real OpenAI Vision API
- [ ] Verify spatial queries performance (<100ms for 10k reports)
- [ ] Fix any failing tests or bugs
- [ ] Achieve 80% backend test coverage

### Tadiwanashe Divine Mphame - Frontend Testing & Integration
- [ ] Run full frontend test suite (unit + property tests)
- [ ] Test all React components with React Testing Library
- [ ] Perform end-to-end testing with Playwright
- [ ] Test complete user flow (register → submit → view)
- [ ] Test offline mode thoroughly
- [ ] Test responsive design on mobile/tablet/desktop
- [ ] Fix any UI bugs or issues
- [ ] Achieve 75% frontend test coverage

### Emmanuel Chidiebere Nzeh - Admin Flow Testing
- [ ] Test admin authentication and RBAC
- [ ] Test heat map with various report densities
- [ ] Test report filtering and clustering
- [ ] Test admin status updates and notifications
- [ ] Test category override and severity adjustment
- [ ] Test internal notes and audit logging
- [ ] Test report archival functionality
- [ ] Verify email/SMS notifications work correctly

### Valeriia Lebedieva - Security & Performance Testing
- [ ] Test authentication on all protected endpoints
- [ ] Verify RBAC with user and admin roles
- [ ] Check for SQL injection vulnerabilities
- [ ] Test rate limiting functionality
- [ ] Perform load testing with 10,000 reports
- [ ] Test duplicate detection accuracy
- [ ] Verify password reset flow security
- [ ] Test API error handling edge cases

---

## Phase 6: Deployment & Documentation (Week 7)

### Brighton Dube - Deployment Setup
- [ ] Create Dockerfile for backend (Python/FastAPI)
- [ ] Create Dockerfile for frontend (React build)
- [ ] Set up Docker Compose for local development
- [ ] Configure production environment variables
- [ ] Set up database backup strategy
- [ ] Deploy to cloud platform (AWS/GCP/Azure)
- [ ] Configure domain and SSL certificates
- [ ] Set up monitoring and logging

### Tadiwanashe Divine Mphame - Frontend Deployment
- [ ] Build production React bundle
- [ ] Optimize bundle size and performance
- [ ] Configure CDN for static assets
- [ ] Test PWA installation on mobile devices
- [ ] Verify offline mode works in production
- [ ] Set up error tracking (Sentry or similar)
- [ ] Test production deployment thoroughly
- [ ] Create user guide for citizens

### Emmanuel Chidiebere Nzeh - Documentation
- [ ] Write comprehensive README.md
- [ ] Document installation instructions
- [ ] Create configuration guide
- [ ] Document all environment variables
- [ ] Write API documentation (supplement OpenAPI)
- [ ] Create admin user guide
- [ ] Document troubleshooting common issues
- [ ] Create video demo/tutorial

### Valeriia Lebedieva - Final QA & Polish
- [ ] Perform final end-to-end testing
- [ ] Test all user flows one more time
- [ ] Verify all features work as specified
- [ ] Check for any remaining bugs
- [ ] Optimize database queries if needed
- [ ] Review code quality and refactor if necessary
- [ ] Ensure all documentation is complete
- [ ] Prepare final project presentation

---

## Notes

- **Weekly Sync**: Team meets every Thursday at 7pm UTC
- **Communication**: Use project Teams channel for updates
- **Blockers**: Report blockers immediately on Teams
- **Documentation**: Update docs as you implement features
- **Git Workflow**: Use feature branches, merge to main after review

---

## Progress Tracking

### Week 1: Setup
- [ ] Brighton: Infrastructure complete
- [ ] Tadiwanashe: Frontend setup complete
- [ ] Emmanuel: Authentication complete
- [ ] Valeriia: API design complete

### Week 2-3: Core Features
- [ ] Brighton: Report service complete
- [ ] Tadiwanashe: Report UI complete
- [ ] Emmanuel: AI integration complete
- [ ] Valeriia: Duplicate detection complete

### Week 4: Admin Features
- [ ] Brighton: Notifications complete
- [ ] Tadiwanashe: Heat map complete
- [ ] Emmanuel: Admin service complete
- [ ] Valeriia: Filtering complete

### Week 5: Advanced Features
- [ ] Brighton: Leaderboard backend complete
- [ ] Tadiwanashe: Offline mode complete
- [ ] Emmanuel: User dashboard complete
- [ ] Valeriia: API validation complete

### Week 6: Testing
- [ ] Brighton: Backend testing complete
- [ ] Tadiwanashe: Frontend testing complete
- [ ] Emmanuel: Admin testing complete
- [ ] Valeriia: Security testing complete

### Week 7: Deployment
- [ ] Brighton: Deployment complete
- [ ] Tadiwanashe: Frontend deployed
- [ ] Emmanuel: Documentation complete
- [ ] Valeriia: Final QA complete

---

**Project Completion Target**: 4 weeks from start date
**Team Size**: 4 members
**Meeting Schedule**: Thursdays 7pm UTC
