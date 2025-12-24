from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

from database import SessionLocal
from models import Ticket
from enums import TicketStatus

router = Router()

@router.callback_query(F.data.startswith("close_ticket:"))
async def close_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        ticket = await session.get(Ticket, ticket_id)

        if not ticket:
            await callback.answer("❌ Тикет не найден", show_alert=True)
            return

        if ticket.status == TicketStatus.CLOSED:
            await callback.answer("ℹ️ Тикет уже закрыт")
            return

        ticket.status = TicketStatus.CLOSED
        ticket.closed_at = datetime.utcnow()
        await session.commit()

    await callback.message.edit_text("✅ Тикет закрыт")
    await callback.answer("Тикет закрыт")
