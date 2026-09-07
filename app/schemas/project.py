from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class ProjectCreate(ProjectBase):
    """
    Create a new project.

    owner_id is deliberately excluded.
    The authenticated user becomes the project owner
    in the service layer.
    """
    model_config = ConfigDict(extra="forbid")


class ProjectUpdate(BaseModel):
    """
    Update an existing project.

    owner_id is not editable through normal project updates.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    status: ProjectStatus | None = None

    model_config = ConfigDict(extra="forbid")


class ProjectResponse(ProjectBase):
    id: UUID
    owner_id: UUID
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)