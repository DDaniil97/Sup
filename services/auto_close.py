import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select

from database import SessionLocal
from models import Ticket
from enums import TicketStatus
from services.notify import notify_user


async def auto_close_tickets(bot):
    while True:
        async with SessionLocal() as session:
            timeout = datetime.utcnow() - timedelta(minutes=15)

            result = await session.execute(
                select(Ticket)
                .where(Ticket.status == TicketStatus.ASSIGNED)
                .where(Ticket.assigned_at < timeout)
            )

            tickets = result.scalars().all()

            for ticket in tickets:
                ticket.status = TicketStatus.CLOSED
                ticket.closed_at = datetime.utcnow()
                await session.commit()

                await notify_user(
                    bot=bot,
                    user_id=ticket.user_telegram_id,
                    text=(
                        f"⏱ Тикет #{ticket.id} закрыт автоматически\n"
                        f"Причина: нет ответа более 15 минут"
                    )
                )

        await asyncio.sleep(60)
