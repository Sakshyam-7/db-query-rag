from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.ticket import (
    create_ticket,
    delete_ticket,
    get_ticket_by_id,
    get_tickets_by_project,
    get_tickets_by_user,
    update_ticket,
)
from app.crud.project import get_project_by_id
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketNotFoundError(Exception):
    """Raised when the requested ticket does not exist."""
    pass


class ProjectNotFoundError(Exception):
    """Raised when the requested project does not exist."""
    pass


class TicketPermissionError(Exception):
    """Raised when a user does not have permission to perform an operation."""
    pass


def get_ticket(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> Ticket:
    """
    Get a ticket by ID. Only the project owner, an admin, or the
    ticket's assignee may view it.
    """
    ticket = get_ticket_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Ticket not found")

    project = get_project_by_id(db, ticket.project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    is_admin = current_user.role == UserRole.ADMIN
    is_project_owner = project.owner_id == current_user.id
    is_assignee = ticket.user_id == current_user.id

    if not (is_admin or is_project_owner or is_assignee):
        raise TicketPermissionError("You do not have permission to view this ticket")

    return ticket


def get_project_tickets(
    db: Session,
    project_id: UUID,
    current_user: User,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Ticket]:
    """
    Get all tickets belonging to a project. Only the project owner or
    an admin may list them.
    """
    project = get_project_by_id(db, project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise TicketPermissionError("You do not have permission to view this project's tickets")

    return get_tickets_by_project(db, project_id, limit=limit, offset=offset)


def get_user_tickets(
    db: Session,
    user_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Ticket]:
    """
    Get all tickets assigned to a specific user. No extra check needed
    here -- callers always pass current_user.id (see router), so a user
    only ever lists their own tickets through this path.
    """
    return get_tickets_by_user(db, user_id, limit=limit, offset=offset)


def create_user_ticket(
    db: Session,
    current_user: User,
    ticket_data: TicketCreate,
) -> Ticket:
    """
    Create a ticket for a project. The authenticated user must be the
    project owner or an admin. The authenticated user automatically
    becomes the assigned user (creator = assignee).
    """
    project = get_project_by_id(db, ticket_data.project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise TicketPermissionError(
            "You do not have permission to create a ticket for this project"
        )

    return create_ticket(
        db,
        title=ticket_data.title,
        description=ticket_data.description,
        project_id=ticket_data.project_id,
        user_id=current_user.id,
        priority=ticket_data.priority,
    )


def update_user_ticket(
    db: Session,
    ticket: Ticket,
    current_user: User,
    ticket_data: TicketUpdate,
) -> Ticket:
    """
    Update a ticket.
    ADMIN or project owner can update any editable field.
    The assignee (ticket.user_id) may update status only.
    """
    project = get_project_by_id(db, ticket.project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    is_admin = current_user.role == UserRole.ADMIN
    is_project_owner = project.owner_id == current_user.id
    is_assignee = ticket.user_id == current_user.id

    if not (is_admin or is_project_owner or is_assignee):
        raise TicketPermissionError("You do not have permission to update this ticket")

    if (
        (ticket_data.title is not None
         or ticket_data.description is not None
         or ticket_data.priority is not None)
        and not (is_admin or is_project_owner)
    ):
        raise TicketPermissionError(
            "Only the project owner or an admin can change these fields"
        )

    if ticket_data.status is not None and not (is_admin or is_project_owner or is_assignee):
        raise TicketPermissionError("You do not have permission to change ticket status")

    return update_ticket(
        db,
        ticket,
        title=ticket_data.title,
        description=ticket_data.description,
        status=ticket_data.status,
        priority=ticket_data.priority,
    )


def delete_user_ticket(
    db: Session,
    ticket: Ticket,
    current_user: User,
) -> None:
    """
    Delete a ticket. Only the project owner or an ADMIN may delete it.
    """
    project = get_project_by_id(db, ticket.project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise TicketPermissionError("You do not have permission to delete this ticket")

    delete_ticket(db, ticket)