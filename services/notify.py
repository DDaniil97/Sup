from aiogram import Bot
from sqlalchemy import select

from models import Manager
from keyboards.manager import take_ticket_kb


async def notify_managers(
    bot: Bot,
    session,
    ticket_id: int,
    user_info: str
):
    result = await session.execute(
        select(Manager).where(Manager.is_active == True)
    )
    managers = result.scalars().all()

    for manager in managers:
        await bot.send_message(
            chat_id=manager.telegram_user_id,
            text=(
                "🆕 Нова заявка\n\n"
                f"{user_info}\n"
                f"Ticket ID: {ticket_id}"
            ),
            reply_markup=take_ticket_kb(ticket_id)
        )
