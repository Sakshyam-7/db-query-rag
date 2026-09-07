from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.user import PasswordChange, UserResponse, UserUpdate
from app.services.user import (
    EmailAlreadyRegisteredError,
    InvalidCurrentPasswordError,
    UserNotFoundError,
    change_user_password,
    change_user_role,
    get_user,
    remove_user,
    update_user_profile,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:

    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        return update_user_profile(
            db,
            current_user,
            user_data,
        )

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )


@router.patch(
    "/me/password",
    response_model=UserResponse,
)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        return change_user_password(
            db,
            current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )

    except InvalidCurrentPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        return get_user(db, user_id)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: UUID,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        user = get_user(db, user_id)

        return change_user_role(
            db,
            user,
            new_role,
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:

    try:
        user = get_user(db, user_id)

        remove_user(
            db,
            user,
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )