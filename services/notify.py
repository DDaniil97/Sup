from aiogram import Bot
from sqlalchemy import select
from models import Manager
from keyboards.manager import take_ticket_kb

print("✅ notify_managers вызывается")


async def notify_managers(
        bot: Bot,
        session,
        ticket_id: int,
        user_info: str
):
    result = await session.execute(
        select(Manager).where(
            Manager.is_active == True,
            Manager.is_manager == True
        )
    )
    managers = result.scalars().all()
    print(f"👥 Найдено менеджеров: {len(managers)}")
    if not managers:
        print("❌ Нет активных менеджеров")
        return

    for manager in managers:
        try:
            await bot.send_message(
                chat_id=manager.telegram_user_id,
                text=(
                    "🆕 Нове звернення\n\n"
                    f"{user_info}\n"
                    f"Ticket ID: {ticket_id}"
                ),
                reply_markup=take_ticket_kb(ticket_id)
            )
        except Exception as e:
            print(
                f"❌ Не удалось отправить менеджеру "
                f"{manager.telegram_user_id}: {e}"
            )


from aiogram import Bot


async def notify_user(bot: Bot, user_id: int, text: str):
    await bot.send_message(chat_id=user_id, text=text)
