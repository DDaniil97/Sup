from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import SessionLocal
from enums import TicketStatus
from models import Ticket, User, Message as TicketMessage
from services.notify import notify_user
from datetime import datetime
from sqlalchemy import select

router = Router()

def close_ticket_keyboard(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Закрыть тикет",
                    callback_data=f"close_ticket:{ticket_id}"
                )
            ]
        ]
    )


def ticket_action_keyboard(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑‍💻 Взять в работу",
                    callback_data=f"take_ticket:{ticket_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📜 История",
                    callback_data=f"history:{ticket_id}"
                )
            ]
        ]
    )


# Команда /dialogs для менеджера (список тикетов)
@router.message(F.text == "/dialogs")
async def dialogs(message: Message):
    async with SessionLocal() as session:
        tickets = (
            await session.execute(
                select(Ticket).where(Ticket.assigned_manager_telegram_id.is_(None))
            )
        ).scalars().all()

    if not tickets:
        await message.answer("📭 Тикетов нет")
        return

    for ticket in tickets:
        await message.answer(
            text=(
                "🆕 Новое обращение\n\n"
                f"👤 Пользователь: {ticket.user_telegram_id}\n"
                f"🎫 Ticket ID: {ticket.id}"
            ),
            reply_markup=ticket_action_keyboard(ticket.id)
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

    await callback.message.edit_text(
        f"🧑‍💻 Тикет в работе\n"
        f"Менеджер: {callback.from_user.full_name}",
        reply_markup=close_ticket_keyboard(ticket.id)
    )

    await callback.answer("✅ Вы взяли тикет в работу")

    # Уведомляем пользователя
    await notify_user(
        bot=callback.bot,
        user_id=ticket.user_telegram_id,
        text=f"ℹ️ Ваш тикет #{ticket.id} взят в работу менеджером {callback.from_user.full_name}"
    )

@router.message(F.text & ~F.text.startswith("/"))
async def manager_message_handler(message: Message, bot: Bot):
    async with SessionLocal() as session:
        state = await session.get(ManagerState, message.from_user.id)

        if not state or not state.active_ticket_id:
            await message.answer("❗ У вас нет активного тикета")
            return

        ticket = await session.get(Ticket, state.active_ticket_id)
        if not ticket or ticket.status != TicketStatus.ASSIGNED:
            await message.answer("❌ Тикет не активен")
            return

        # сохраняем сообщение менеджера
        msg_record = TicketMessage(
            ticket_id=ticket.id,
            from_role="manager",
            message_type="text",
            text=message.text,
            telegram_message_id=message.message_id
        )
        session.add(msg_record)
        await session.commit()

        # отправляем пользователю
        await bot.send_message(
            chat_id=ticket.user_telegram_id,
            text=f"🧑‍💼 Менеджер:\n{message.text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="✅ Закрыть тикет",
                        callback_data=f"close_ticket:{ticket.id}"
                    )
                ]]
            )
        )

@router.callback_query(F.data.startswith("close_ticket:"))
async def manager_close_ticket(callback: CallbackQuery):
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

    await callback.message.edit_text(f"✅ Тикет #{ticket_id} закрыт")
    await callback.answer("Тикет закрыт")

    # уведомляем пользователя
    await callback.bot.send_message(
        ticket.user_telegram_id,
        "❌ Ваш тикет был закрыт"
    )

@router.callback_query(F.data.startswith("history:"))
async def history_handler(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        result = await session.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.created_at)
        )
        messages = result.scalars().all()

    if not messages:
        await callback.answer("История пуста", show_alert=True)
        return

    text_lines = []
    for msg in messages:
        role = "👤 Пользователь" if msg.from_role == "user" else "🧑‍💼 Менеджер"
        content = msg.text or msg.caption or "📎 Вложение"
        text_lines.append(f"{role}: {content}")

    history_text = "\n\n".join(text_lines)

    # Telegram лимит ~4096
    for chunk in [history_text[i:i+4000] for i in range(0, len(history_text), 4000)]:
        await callback.message.answer(chunk)

    await callback.answer()
