"""
Auth service layer: registration, authentication, and token issuance.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.core.jwt import create_access_token
from app.core.refresh_token_utils import generate_refresh_token, hash_refresh_token
from app.core.security import hash_password, verify_password
from app.crud.user import create_user, get_user_by_email
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


def register_user(db: Session, user_data: UserCreate) -> User:
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError(f"Email {user_data.email} is already registered")

    password_hash = hash_password(user_data.password)
    return create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
    )


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        raise InvalidCredentialsError("Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    return user


def create_user_tokens(db: Session, user_id: UUID) -> dict[str, str]:
    access_token = create_access_token(user_id)

    raw_refresh_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db.add(RefreshToken(token_hash=token_hash, user_id=user_id, expires_at=expires_at))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, raw_refresh_token: str) -> dict[str, str]:
    token_hash = hash_refresh_token(raw_refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if record is None:
        raise InvalidRefreshTokenError("Invalid refresh token")
    if record.revoked_at is not None:
        raise InvalidRefreshTokenError("Refresh token has been revoked")
    if record.expires_at < datetime.now(timezone.utc):
        raise InvalidRefreshTokenError("Refresh token has expired")

    new_access_token = create_access_token(record.user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
    }


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()