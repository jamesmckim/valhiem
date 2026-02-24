# backend/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Custom
from auth import create_access_token, verify_password, get_current_user_id, get_password_hash
from database import User
from dependencies import get_db
from schemas import UserRegister, UserProfile

router = APIRouter(tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # 1. Check for duplicates
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered"
        )
    
    # 2. Hash Password (uses your auth.py bcrypt logic)
    hashed_pw = get_password_hash(user.password)
    
    # 3. Create User
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        credits=0
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        
    return {"message": "Account created successfully", "user_id": new_user.id}

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
    
@router.get("/users/me", response_model=UserProfile)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    """Returns the profile of the currently logged-in user."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user