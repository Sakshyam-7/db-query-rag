"""
Ticket routes.
Handles: create, list mine, list by project, get one, update, delete.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services.ticket import (
    ProjectNotFoundError,
    TicketNotFoundError,
    TicketPermissionError,
    create_user_ticket,
    delete_user_ticket,
    get_project_tickets,
    get_ticket,
    get_user_tickets,
    update_user_ticket,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_route(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        return create_user_ticket(db, current_user, ticket_data)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except TicketPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create a ticket for this project")


@router.get(
    "",
    response_model=list[TicketResponse],
)
def list_my_tickets_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    return get_user_tickets(db, current_user.id)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket_route(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        return get_ticket(db, ticket_id, current_user)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except TicketPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this ticket")


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket_route(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        ticket = get_ticket(db, ticket_id, current_user)
        return update_user_ticket(db, ticket, current_user, ticket_data)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except TicketPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_route(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        ticket = get_ticket(db, ticket_id, current_user)
        delete_user_ticket(db, ticket, current_user)
    except TicketNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except TicketPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this ticket")