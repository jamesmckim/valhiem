from database import SessionLocal, init_db, User
from auth import get_password_hash

def seed_admin():
    # 1. Initialize tables if they don't exist
    init_db()
    
    db = SessionLocal()
    
    # 2. Check if admin already exists to avoid duplicates
    existing_user = db.query(User).filter(User.username == "admin").first()
    if existing_user:
        print("Admin user already exists. Skipping...")
        return

    # 3. Create the admin user
    # We give them 100 credits to start testing!
    new_user = User(
        username="admin",
        hashed_password=get_password_hash("password123"), # Change this later!
        credits=100.0
    )
    
    db.add(new_user)
    db.commit()
    print("Successfully created user: admin with 100 credits.")
    db.close()

if __name__ == "__main__":
    seed_admin()