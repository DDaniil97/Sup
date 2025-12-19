from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import SessionLocal
from services.tickets import get_active_tickets_for_manager

router = Router()


@router.message(Command("dialogs"))
async def manager_dialogs(message, bot):
    async with SessionLocal() as session:
        tickets = await get_active_tickets_for_manager(
            session, message.from_user.id
        )

        if not tickets:
            await message.answer("У вас нет активных диалогов")
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"👤 Пользователь {t.user_telegram_id}",
                        callback_data=f"select_ticket:{t.id}"
                    )
                ]
                for t in tickets
            ]
        )

        await message.answer(
            "📂 Ваши активные диалоги:",
            reply_markup=kb
        )
