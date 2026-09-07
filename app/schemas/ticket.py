from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketPriority, TicketStatus


class TicketBase(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class TicketCreate(TicketBase):
    """
    Create a new ticket.

    user_id is deliberately excluded.
    The authenticated user becomes the ticket creator.

    status is also excluded because every new ticket
    starts as OPEN.
    """

    project_id: UUID
    priority: TicketPriority = TicketPriority.MEDIUM

    model_config = ConfigDict(extra="forbid")


class TicketUpdate(BaseModel):
    """
    Update an existing ticket.

    user_id and project_id are not editable through
    the normal ticket update operation.
    """

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    status: TicketStatus | None = None
    priority: TicketPriority | None = None

    model_config = ConfigDict(extra="forbid")


class TicketResponse(TicketBase):
    id: UUID
    user_id: UUID
    project_id: UUID
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)