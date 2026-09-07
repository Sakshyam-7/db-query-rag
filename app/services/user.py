

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password

from app.crud.user import (
    delete_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
    update_user_password_hash,
    update_user_role,
)
from app.models.user import User, UserRole
from app.schemas.user import UserUpdate


class UserNotFoundError(Exception):
    """
    Raised when the requested user does not exist.
    """

    pass


class EmailAlreadyRegisteredError(Exception):
    """
    Raised when an email is already used by another user.
    """

    pass


class InvalidCurrentPasswordError(Exception):
    """
    Raised when the supplied current password is incorrect.
    """

    pass


def get_user(
    db: Session,
    user_id: UUID,
) -> User:
    """
    Get a user by ID.

    Raises UserNotFoundError if the user does not exist.
    """

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise UserNotFoundError(
            "User not found"
        )

    return user


def update_user_profile(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:
    """
    Update a user's profile.

    Users can update their name and email.
    Role and password are handled separately.
    """

    if user_data.email is not None:
        existing_user = get_user_by_email(
            db,
            user_data.email,
        )

        if (
            existing_user is not None
            and existing_user.id != user.id
        ):
            raise EmailAlreadyRegisteredError(
                "Email is already registered"
            )

    return update_user(
        db,
        user,
        name=user_data.name,
        email=user_data.email,
    )


def change_user_role(
    db: Session,
    user: User,
    new_role: UserRole,
) -> User:
    """
    Change a user's role.

    Authorization must be checked before calling this function.
    Typically, only an ADMIN should be allowed to call it.
    """

    return update_user_role(
        db,
        user,
        new_role,
    )


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    """
    Change a user's password.

    The current password must be verified before the new
    password is hashed and stored.
    """

    if not verify_password(
        current_password,
        user.password_hash,
    ):
        raise InvalidCurrentPasswordError(
            "Current password is incorrect"
        )

    new_password_hash = hash_password(
        new_password,
    )

    return update_user_password_hash(
        db,
        user,
        new_password_hash,
    )


def remove_user(
    db: Session,
    user: User,
) -> None:
    """
    Delete a user.

    Authorization and any related-record rules must be
    handled before calling this function.
    """

    delete_user(
        db,
        user,
    )
    