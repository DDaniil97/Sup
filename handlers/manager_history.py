from aiogram import Router
from aiogram.filters import Command

from database import SessionLocal
from services.history import get_ticket_history
from services.manager_state import get_manager_state
from enums import MessageRole
router = Router()


@router.message(Command("history"))
async def show_history(message):
    async with SessionLocal() as session:
        state = await get_manager_state(
            session, message.from_user.id
        )

        if not state.active_ticket_id:
            await message.answer("Диалог не выбран")
            return

        history = await get_ticket_history(
            session, state.active_ticket_id
        )

        text = "📜 История:\n\n"
        for msg in history:
            who = "👤" if msg.from_role == MessageRole.USER.value else "🧑‍💼"
            if msg.text:
                text += f"{who} {msg.text}\n"

        await message.answer(text[-4000:])
