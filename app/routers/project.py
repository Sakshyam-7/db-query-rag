"""
Project routes.
Handles: create, list (own), get one, update, delete.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import (
    ProjectNotFoundError,
    ProjectPermissionError,
    create_user_project,
    delete_user_project,
    get_project,
    get_user_projects,
    update_user_project,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_route(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    return create_user_project(db, current_user.id, project_data)


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    return get_user_projects(db, current_user.id)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project_route(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    try:
        return get_project(db, project_id, current_user.id, current_user.role)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except ProjectPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this project")


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project_route(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    try:
        project = get_project(db, project_id, current_user.id, current_user.role)
        return update_user_project(db, project, current_user.id, current_user.role, project_data)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except ProjectPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this project")


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project_route(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        project = get_project(db, project_id, current_user.id, current_user.role)
        delete_user_project(db, project, current_user.id, current_user.role)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except ProjectPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")