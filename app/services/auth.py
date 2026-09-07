"""
Auth service layer: registration, authentication, and token issuance.

No FastAPI imports here (no HTTPException) -- this stays HTTP-agnostic.
Routes are the only layer that should translate these exceptions into
actual HTTP responses.
"""
from uuid import UUID

import jwt as pyjwt
from sqlalchemy.orm import Session

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_and_validate_token,
)
from app.core.security import hash_password, verify_password
from app.crud.user import create_user, get_user_by_email
from app.models.user import User
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    """Raised when signup is attempted with an email already in use."""
    pass


class InvalidCredentialsError(Exception):
    """
    Raised for ANY login failure -- unknown email or wrong password.
    Deliberately a single exception for both cases so the caller can't
    leak which one occurred (prevents email enumeration).
    """
    pass


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is invalid, expired, or the wrong type."""
    pass


def register_user(db: Session, user_data: UserCreate) -> User:
    """
    Register a new user. New users are always created as MEMBER
    (enforced inside create_user, not here).
    """
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError(f"Email {user_data.email} is already registered")

    password_hash = hash_password(user_data.password)
    user = create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
    )
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user using email and password.
    Raises InvalidCredentialsError for any failure -- never distinguishes
    "no such user" from "wrong password" to the caller.
    """
    user = get_user_by_email(db, email)
    if user is None:
        raise InvalidCredentialsError("Invalid email or password")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")

    return user


def create_user_tokens(user_id: UUID) -> dict[str, str]:
    """
    Create an access + refresh token pair for an authenticated user.
    """
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    Validate a refresh token and issue a new access token.
    Does NOT issue a new refresh token here (no rotation) -- the same
    refresh token stays valid until its own expiry.
    """
    try:
        payload = decode_and_validate_token(refresh_token, expected_type="refresh")
    except pyjwt.InvalidTokenError:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    user_id = UUID(payload["sub"])
    new_access_token = create_access_token(user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }