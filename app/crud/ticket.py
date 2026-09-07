from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketPriority, TicketStatus


def get_ticket_by_id(
    db: Session,
    ticket_id: UUID,
) -> Ticket | None:
    """
    Get a ticket by its UUID.
    """
    return db.get(Ticket, ticket_id)


def get_tickets(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Ticket]:
    """
    Get tickets with pagination.
    """
    statement = (
        select(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_tickets_by_project(
    db: Session,
    project_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Ticket]:
    """
    Get tickets belonging to a specific project.
    """
    statement = (
        select(Ticket)
        .where(Ticket.project_id == project_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_tickets_by_user(
    db: Session,
    user_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Ticket]:
    """
    Get tickets assigned to a specific user.
    """
    statement = (
        select(Ticket)
        .where(Ticket.user_id == user_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def create_ticket(
    db: Session,
    *,
    title: str,
    description: str | None,
    project_id: UUID,
    user_id: UUID,
    priority: TicketPriority = TicketPriority.MEDIUM,
) -> Ticket:
    
    ticket = Ticket(
        title=title,
        description=description,
        project_id=project_id,
        user_id=user_id,
        priority=priority,
    )
    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        raise
    return ticket


def update_ticket(
    db: Session,
    ticket: Ticket,
    *,
    title: str | None = None,
    description: str | None = None,
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
) -> Ticket:
    
    if title is not None:
        ticket.title = title
    if description is not None:
        ticket.description = description
    if status is not None:
        ticket.status = status
    if priority is not None:
        ticket.priority = priority
    try:
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        raise
    return ticket


def delete_ticket(
    db: Session,
    ticket: Ticket,
) -> None:
    """
    Delete a ticket.
    """
    try:
        db.delete(ticket)
        db.commit()
    except Exception:
        db.rollback()
        raise