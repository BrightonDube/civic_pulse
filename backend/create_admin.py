"""
Script to create an admin user for testing.
"""
from app.core.database import SessionLocal
from app.models.user import User

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@civicpulse.com").first()
        
        if admin:
            print(f"Admin user already exists:")
            print(f"  Email: {admin.email}")
            print(f"  Role: {admin.role}")
            print(f"\nUse password: admin123")
        else:
            # Create new admin user
            admin = User(
                email="admin@civicpulse.com",
                phone="+1234567890",
                role="admin"
            )
            admin.set_password("admin123")
            
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            print("Admin user created successfully!")
            print(f"  Email: {admin.email}")
            print(f"  Password: admin123")
            print(f"  Role: {admin.role}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
