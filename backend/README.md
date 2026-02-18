# CivicPulse Backend

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example` and update values

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## Test Credentials

### Admin User
- **Email:** admin@civicpulse.com
- **Password:** admin123
- **Role:** admin
- **Access:** Full admin dashboard, heat map, report management, status updates

### Regular User
- **Email:** bizpilot16@gmail.com
- **Password:** (your password)
- **Role:** user
- **Access:** Submit reports, view own reports, upvote reports, view leaderboard

To create the admin user, run:
```bash
python create_admin.py
```
