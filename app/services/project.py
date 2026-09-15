"""
Project service layer.
Handles project-related business rules and coordinates
project CRUD operations.
This layer is HTTP-agnostic.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.project import (
    create_project,
    delete_project,
    get_project_by_id,
    get_projects_by_owner,
    update_project,
)
from app.models.project import Project, ProjectStatus
from app.models.user import UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectNotFoundError(Exception):
    """Raised when the requested project does not exist."""
    pass


class ProjectPermissionError(Exception):
    """Raised when a user does not have permission to perform
    an operation on a project."""
    pass


def _is_owner_or_admin(project: Project, user_id: UUID, user_role: UserRole) -> bool:
    return user_role == UserRole.ADMIN or project.owner_id == user_id


def get_project(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    user_role: UserRole,
) -> Project:
    """
    Get a project by ID. Only the owner or an admin may view it.
    """
    project = get_project_by_id(db, project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    if not _is_owner_or_admin(project, user_id, user_role):
        raise ProjectPermissionError("You do not have permission to view this project")

    return project


def get_user_projects(
    db: Session,
    user_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    return get_projects_by_owner(db, user_id, limit=limit, offset=offset)


def create_user_project(
    db: Session,
    user_id: UUID,
    project_data: ProjectCreate,
) -> Project:
    return create_project(
        db,
        name=project_data.name,
        description=project_data.description,
        owner_id=user_id,
    )


def update_user_project(
    db: Session,
    project: Project,
    user_id: UUID,
    user_role: UserRole,
    project_data: ProjectUpdate,
) -> Project:
    if not _is_owner_or_admin(project, user_id, user_role):
        raise ProjectPermissionError("You do not have permission to update this project")

    return update_project(
        db,
        project,
        name=project_data.name,
        description=project_data.description,
        status=project_data.status,
    )


def delete_user_project(
    db: Session,
    project: Project,
    user_id: UUID,
    user_role: UserRole,
) -> None:
    if not _is_owner_or_admin(project, user_id, user_role):
        raise ProjectPermissionError("You do not have permission to delete this project")

    delete_project(db, project)