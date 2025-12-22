from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import SessionLocal
from models import Ticket, User, Message as TicketMessage
from services.notify import notify_user
from datetime import datetime
from sqlalchemy import select

router = Router()

# Кнопка "Взять в работу" для каждого нового тикета
def take_ticket_keyboard(ticket_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🧑‍💻 Взять в работу",
                callback_data=f"take_ticket:{ticket_id}"
            )]
        ]
    )
    return keyboard

# Команда /dialogs для менеджера (список тикетов)
@router.message(F.text.startswith("/dialogs"))
async def dialogs(message: Message):
    async with SessionLocal() as session:
        result = await session.execute(
            Ticket.__table__.select().where(Ticket.assigned_manager_telegram_id == None)
        )
        tickets = result.fetchall()

    if not tickets:
        await message.answer("Список текущих тикетов пуст.")
        return

    for row in tickets:
        ticket = row[0]
        await message.answer(
            f"🆕 Новое обращение\n\n"
            f"👤 Пользователь\n"
            f"ID: {ticket.user_telegram_id}\n"
            f"Ticket ID: {ticket.id}",
            reply_markup=take_ticket_keyboard(ticket.id)
        )

# Callback на кнопку "Взять в работу"
@router.callback_query(F.data.startswith("take_ticket:"))
async def take_ticket_handler(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        # Получаем тикет
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            await callback.answer("❌ Тикет не найден", show_alert=True)
            return

        if ticket.assigned_manager_telegram_id is not None:
            await callback.answer("❌ Этот тикет уже взят", show_alert=True)
            return

        # Присваиваем менеджера
        ticket.assigned_manager_telegram_id = callback.from_user.id
        ticket.assigned_at = datetime.utcnow()

        # Получаем все сообщения пользователя
        user_messages = await session.execute(
            select(TicketMessage).where(
                TicketMessage.ticket_id == ticket.id,
                TicketMessage.from_role == "user"
            )
        )
        user_messages = user_messages.scalars().all()  # <-- scalars() вернёт объекты Message

        # Сохраняем изменения тикета
        await session.commit()

    # Отправляем менеджеру все сообщения пользователя
    for msg in user_messages:
        text = msg.text or msg.caption or "📎 Сообщение без текста"
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"👤 Пользователь:\n{text}"
        )

    # Меняем текст сообщения менеджера
    await callback.message.edit_text(
        f"🧑‍💻 Тикет взят в работу менеджером {callback.from_user.full_name}"
    )
    await callback.answer("✅ Вы взяли тикет в работу")

    # Уведомляем пользователя
    await notify_user(
        bot=callback.bot,
        user_id=ticket.user_telegram_id,
        text=f"ℹ️ Ваш тикет #{ticket.id} взят в работу менеджером {callback.from_user.full_name}"
    )

# Хэндлер для сообщений менеджера
@router.message(F.text & ~F.text.startswith("/"))
async def manager_message_handler(message: Message):
    await message.answer("📩 Для работы с тикетами используйте /dialogs")
