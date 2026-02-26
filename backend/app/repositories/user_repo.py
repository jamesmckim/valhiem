# /backend/app/repositories/user_repo.py
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Adjust import based on where you move your models (e.g., app.domain.models)
from database import User 
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their unique username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their unique email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username_or_email(self, username: str, email: str) -> User | None:
        """
        Checks if a user exists with either the given username OR email.
        Used primarily during registration to check for duplicates.
        """
        return self.db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()
     # Inside UserRepository class
    def add_credits(self, user_id: str, amount: int):
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += amount
            self.db.commit()
            self.db.refresh(user)