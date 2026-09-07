from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
   


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")
    # Server-side (service layer), role is hardcoded to UserRole.MEMBER
    # when constructing the User object — never taken from client input.


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    model_config = ConfigDict(extra="forbid")


class UserRoleUpdate(BaseModel):
    """Admin-only. Route must be gated by an admin-permission check
    BEFORE this schema is processed."""
    role: UserRole
    model_config = ConfigDict(extra="forbid")



class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)