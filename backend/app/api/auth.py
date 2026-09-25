import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.db_models import User
from app.core.auth_utils import (
    hash_password, verify_password, create_access_token, decode_access_token, ADMIN_EMAIL
)

router = APIRouter()
security = HTTPBearer(auto_error=False)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


from typing import Optional

class AuthRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that validates JWT access token from Authorization header
    and returns the authenticated User object.
    Raises HTTP 401 if missing, invalid, or expired.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user identity.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auto-bootstrap admin role if email matches ADMIN_EMAIL
    if ADMIN_EMAIL and user.email.lower() == ADMIN_EMAIL and not user.is_admin:
        user.is_admin = True
        db.commit()
        db.refresh(user)

    return user


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(request: AuthRequest, db: Session = Depends(get_db)):
    """
    Registers a new user with hashed password and returns a JWT access token.
    """
    email_clean = request.email.strip().lower() if request.email else ""
    if not email_clean or not EMAIL_REGEX.match(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )

    if not request.password or len(request.password.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty."
        )

    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    is_admin_flag = False
    if ADMIN_EMAIL and email_clean == ADMIN_EMAIL:
        is_admin_flag = True

    full_name_clean = request.full_name.strip() if request.full_name else None

    new_user = User(
        full_name=full_name_clean,
        email=email_clean,
        hashed_password=hash_password(request.password),
        is_admin=is_admin_flag
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name or new_user.email.split("@")[0].capitalize(),
            "email": new_user.email,
            "is_admin": new_user.is_admin
        }
    }


@router.post("/auth/login", status_code=status.HTTP_200_OK)
def login(request: AuthRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user against hashed password and returns a JWT access token.
    """
    email_clean = request.email.strip().lower() if request.email else ""
    if not email_clean or not request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Check ADMIN_EMAIL bootstrap
    if ADMIN_EMAIL and email_clean == ADMIN_EMAIL and not user.is_admin:
        user.is_admin = True
        db.commit()
        db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name or user.email.split("@")[0].capitalize(),
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


@router.get("/auth/me", status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns authenticated user metadata based on active JWT token.
    """
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name or current_user.email.split("@")[0].capitalize(),
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }
    }
