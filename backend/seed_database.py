"""
Database seeding script for CivicPulse.
Creates test users including admin and regular users.

Usage:
  Local:   python seed_database.py
  Railway: railway run python seed_database.py --service backend
"""
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.report import Report, Base


def seed_users(db):
    """Seed test users into the database."""
    
    users_to_create = [
        {
            "email": "admin@civicpulse.com",
            "password": "admin123",
            "phone": "+1234567890",
            "role": "admin",
            "email_verified": True
        },
        {
            "email": "bizpilot16@gmail.com",
            "password": "testuser123",
            "phone": "+1987654321",
            "role": "user",
            "email_verified": True
        },
        {
            "email": "testuser@civicpulse.com",
            "password": "testuser123",
            "phone": "+1122334455",
            "role": "user",
            "email_verified": True
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for user_data in users_to_create:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing:
            print(f"  [EXISTS] {user_data['email']} (role: {existing.role})")
            existing_count += 1
        else:
            user = User(
                email=user_data["email"],
                phone=user_data["phone"],
                role=user_data["role"],
                email_verified=user_data["email_verified"]
            )
            user.set_password(user_data["password"])
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"  [CREATED] {user_data['email']} (role: {user_data['role']})")
            created_count += 1
    
    return created_count, existing_count


def main():
    print("=" * 50)
    print("CivicPulse Database Seeding")
    print("=" * 50)
    
    # Check database connection
    db_url = os.getenv("DATABASE_URL", "Not set")
    if "postgresql" in db_url:
        print(f"Database: PostgreSQL (Railway)")
    elif "sqlite" in db_url:
        print(f"Database: SQLite (Local)")
    else:
        print(f"Database: {db_url[:30]}...")
    
    print()
    
    # Create tables if they don't exist
    print("Ensuring tables exist...")
    Base.metadata.create_all(bind=engine)
    print("  Tables ready!")
    print()
    
    # Seed database
    db = SessionLocal()
    try:
        print("Seeding users...")
        created, existing = seed_users(db)
        
        print()
        print("-" * 50)
        print(f"Summary: {created} created, {existing} already existed")
        print("-" * 50)
        print()
        print("Test Credentials:")
        print("  Admin:  admin@civicpulse.com / admin123")
        print("  User:   testuser@civicpulse.com / testuser123")
        print()
        print("Seeding complete!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
