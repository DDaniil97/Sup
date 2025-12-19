from aiogram import Router
from aiogram.filters import Command

from database import SessionLocal
from enums import TicketStatus
from models import Ticket
from services.manager_state import get_manager_state

router = Router()


@router.message(Command("close"))
async def close_ticket(message):
    async with SessionLocal() as session:
        state = await get_manager_state(
            session, message.from_user.id
        )

        if not state.active_ticket_id:
            await message.answer("Нет активного диалога")
            return

        ticket = await session.get(
            Ticket, state.active_ticket_id
        )

        ticket.status = TicketStatus.CLOSED
        state.active_ticket_id = None

        await session.commit()

        await message.answer("✅ Диалог закрыт")
