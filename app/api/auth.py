"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.schemas.auth_schemas import SignupRequest, LoginRequest, AuthResponse, UserResponse
from app.core.auth_utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(signup_data.password)
    new_user = User(
        email=signup_data.email,
        name=signup_data.name,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=AuthResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.password_hash or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout():
    """Logout endpoint (client-side token removal)."""
    # In a JWT-based system, logout is typically handled client-side
    # by removing the token from storage
    return {"message": "Successfully logged out"}
