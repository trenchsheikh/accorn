"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
