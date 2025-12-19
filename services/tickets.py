from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from models import Ticket
from enums import TicketStatus


async def assign_manager_atomic(
        session: AsyncSession,
        ticket_id: int,
        manager_id: int
) -> bool:
    """
    Возвращает True, если менеджер успешно назначен
    False — если заявку уже взяли
    """

    result = await session.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .with_for_update()
    )

    ticket = result.scalar_one_or_none()

    if not ticket:
        return False

    if ticket.status != TicketStatus.WAITING_MANAGER:
        return False

    ticket.status = TicketStatus.ASSIGNED
    ticket.assigned_manager_telegram_id = manager_id
    ticket.assigned_at = func.now()

    await session.commit()
    return True


async def get_active_ticket_for_user(session, user_id: int):
    result = await session.execute(
        select(Ticket).where(
            Ticket.user_telegram_id == user_id,
            Ticket.status == TicketStatus.ASSIGNED
        )
    )
    return result.scalar_one_or_none()


async def get_active_tickets_for_manager(session, manager_id: int):
    result = await session.execute(
        select(Ticket).where(
            Ticket.assigned_manager_telegram_id == manager_id,
            Ticket.status == TicketStatus.ASSIGNED
        )
    )
    return result.scalars().all()
