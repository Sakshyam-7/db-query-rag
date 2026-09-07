from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    """
    Get a user by UUID.
    """
    return db.get(User, user_id)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """
    Get a user by email.
    """
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
) -> User:
    """
    Create and persist a new user.
    role is explicitly set to MEMBER here -- not accepted as an argument.
    Email uniqueness must be checked by the caller (service layer)
    before calling this.
    """
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role=UserRole.MEMBER,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user


def update_user(
    db: Session,
    user: User,
    *,
    name: str | None = None,
    email: str | None = None,
) -> User:
    """
    Update editable user fields (name, email).
    Email uniqueness (if email is being changed) must be checked by the
    caller (service layer) before calling this.
    """
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user


def update_user_role(
    db: Session,
    user: User,
    role: UserRole,
) -> User:
    """
    Update a user's role.
    Authorization must be handled by the service layer.
    """
    user.role = role
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user


def update_user_password_hash(
    db: Session,
    user: User,
    password_hash: str,
) -> User:
    """
    Update a user's password hash.
    The password must already be hashed before this function is called.
    """
    user.password_hash = password_hash
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user


def delete_user(
    db: Session,
    user: User,
) -> None:
    """
    Delete a user.
    """
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise