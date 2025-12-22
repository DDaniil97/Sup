from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Ticket
from enums import TicketStatus


async def get_active_ticket_for_user(
    session: AsyncSession,
    user_id: int
) -> Ticket | None:
    """
    Возвращает последний активный тикет пользователя
    """
    result = await session.execute(
        select(Ticket)
        .where(
            Ticket.user_telegram_id == user_id,
            Ticket.status.in_([
                TicketStatus.WAITING_MANAGER,
                TicketStatus.ASSIGNED
            ])
        )
        .order_by(Ticket.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_active_tickets_for_manager(
    session: AsyncSession,
    manager_id: int
) -> list[Ticket]:
    """
    Возвращает все активные заявки менеджера
    """
    result = await session.execute(
        select(Ticket)
        .where(
            Ticket.assigned_manager_telegram_id == manager_id,
            Ticket.status == TicketStatus.ASSIGNED
        )
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def assign_manager_atomic(
    session: AsyncSession,
    ticket_id: int,
    manager_id: int
) -> bool:
    """
    Атомарно назначает менеджера на заявку
    """
    ticket = await session.get(Ticket, ticket_id)

    if not ticket or ticket.status != TicketStatus.WAITING_MANAGER:
        return False

    ticket.assigned_manager_telegram_id = manager_id
    ticket.status = TicketStatus.ASSIGNED

    await session.commit()
    return True

