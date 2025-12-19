from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from database import SessionLocal
from services.manager_state import get_manager_state
from services.tickets import assign_manager_atomic, get_active_tickets_for_manager

from services.messages import save_message
from enums import MessageRole, MessageType

router = Router()


@router.callback_query(F.data.startswith("take_ticket:"))
async def take_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])
    manager_id = callback.from_user.id

    async with SessionLocal() as session:
        success = await assign_manager_atomic(
            session,
            ticket_id,
            manager_id
        )

    if success:
        await callback.message.edit_text(
            "✅ Ви взяли заявку в роботу"
        )
        await callback.answer("Заявка закріплена за вами")
    else:
        await callback.answer(
            "❌ Заявку вже взяв інший менеджер",
            show_alert=True
        )


@router.message(F.content_type.in_({"text", "photo", "video", "voice", "sticker"}))
async def manager_message_handler(message, bot):
    async with SessionLocal() as session:
        state = await get_manager_state(
            session, message.from_user.id
        )

        if not state.active_ticket_id:
            await message.answer(
                "⚠️ Выберите диалог через /dialogs"
            )
            return

        ticket = await session.get(
            Ticket, state.active_ticket_id
        )

        if not ticket:
            await message.answer("Тикет не найден")
            return

        user_id = ticket.user_telegram_id

        if message.text:
            await bot.send_message(user_id, message.text)

            await save_message(
                session,
                ticket.id,
                MessageRole.MANAGER,
                MessageType.TEXT,
                message.message_id,
                text=message.text
            )

        elif message.photo:
            photo = message.photo[-1]
            await bot.send_photo(
                user_id,
                photo.file_id,
                caption=message.caption
            )

            await save_message(
                session,
                ticket.id,
                MessageRole.MANAGER,
                MessageType.PHOTO,
                message.message_id,
                caption=message.caption,
                file_id=photo.file_id
            )

        elif message.video:
            await bot.send_video(
                user_id,
                message.video.file_id,
                caption=message.caption
            )

            await save_message(
                session,
                ticket.id,
                MessageRole.MANAGER,
                MessageType.VIDEO,
                message.message_id,
                caption=message.caption,
                file_id=message.video.file_id
            )

        elif message.voice:
            await bot.send_voice(
                user_id,
                message.voice.file_id
            )

            await save_message(
                session,
                ticket.id,
                MessageRole.MANAGER,
                MessageType.VOICE,
                message.message_id,
                file_id=message.voice.file_id
            )

        elif message.sticker:
            await bot.send_sticker(
                user_id,
                message.sticker.file_id
            )

            await save_message(
                session,
                ticket.id,
                MessageRole.MANAGER,
                MessageType.STICKER,
                message.message_id,
                file_id=message.sticker.file_id
            )
