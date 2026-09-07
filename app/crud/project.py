

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus


def get_project_by_id(
    db: Session,
    project_id: UUID,
) -> Project | None:
    """
    Get a project by its UUID.
    """
    return db.get(Project, project_id)


def get_projects(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    """
    Get projects with pagination.
    """

    statement = (
        select(Project)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(db.scalars(statement).all())


def get_projects_by_owner(
    db: Session,
    owner_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    """
    Get projects owned by a specific user.
    """

    statement = (
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(db.scalars(statement).all())


def create_project(
    db: Session,
    *,
    name: str,
    description: str | None,
    owner_id: UUID,
) -> Project:
    """
    Create and persist a new project.

    Authorization is handled by the service layer.
    New projects use the model's default status.
    """

    project = Project(
        name=name,
        description=description,
        owner_id=owner_id,
    )

    try:
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception:
        db.rollback()
        raise

    return project


def update_project(
    db: Session,
    project: Project,
    *,
    name: str | None = None,
    description: str | None = None,
    status: ProjectStatus | None = None,
) -> Project:
    """
    Update project fields.

    Authorization must be checked by the service layer.
    """

    if name is not None:
        project.name = name

    if description is not None:
        project.description = description

    if status is not None:
        project.status = status

    try:
        db.commit()
        db.refresh(project)
    except Exception:
        db.rollback()
        raise

    return project


def delete_project(
    db: Session,
    project: Project,
) -> None:
    """
    Delete a project.
    """

    try:
        db.delete(project)
        db.commit()
    except Exception:
        db.rollback()
        raise