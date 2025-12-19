from aiogram import F, Router

from database import SessionLocal
from services.manager_state import set_active_ticket
from sqlalchemy import select
from models import Ticket

router = Router()


@router.callback_query(F.data.startswith("select_ticket:"))
async def select_ticket(callback, bot):
    ticket_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        ticket = await session.get(Ticket, ticket_id)

        if not ticket:
            await callback.answer("Тикет не найден")
            return

        await set_active_ticket(
            session,
            callback.from_user.id,
            ticket_id
        )

        await callback.message.answer(
            f"✅ Вы отвечаете пользователю {ticket.user_telegram_id}"
        )

        await callback.answer()
