from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import SessionLocal
from models import User, Ticket
from enums import TicketStatus, MessageRole, MessageType


from services.tickets import get_active_ticket_for_user
from services.messages import save_message


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)

        if not user:
            user = User(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            session.add(user)

        ticket = Ticket(
            user_telegram_id=message.from_user.id,
            status=TicketStatus.WAITING_MANAGER
        )
        session.add(ticket)

        await session.commit()

    await message.answer(
        "ОТРИМАТИ БОНУС\n\n"
        "Заявка прийнята. Підключаємо менеджера. Очікуйте."
    )


from services.notify import notify_managers


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    async with SessionLocal() as session:
        user = await session.get(User, message.from_user.id)

        if not user:
            user = User(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            session.add(user)

        ticket = Ticket(
            user_telegram_id=message.from_user.id,
            status=TicketStatus.WAITING_MANAGER
        )
        session.add(ticket)
        await session.commit()

        user_info = (
            f"👤 {message.from_user.first_name}\n"
            f"@{message.from_user.username}\n"
            f"ID: {message.from_user.id}\n"
            f"⏰ {ticket.created_at}"
        )

        await notify_managers(bot, session, ticket.id, user_info)

    await message.answer(
        "ОТРИМАТИ БОНУС\n\n"
        "Заявка прийнята. Підключаємо менеджера. Очікуйте."
    )



@router.message(F.content_type.in_({"text", "photo", "video", "voice", "sticker"}))
async def user_message_handler(message: Message, bot):
    async with SessionLocal() as session:
        ticket = await get_active_ticket_for_user(
            session, message.from_user.id
        )

        if not ticket:
            await message.answer(
                "⏳ Очікуйте, менеджер ще не підключився"
            )
            return

        manager_id = ticket.assigned_manager_telegram_id

        # === ТЕКСТ ===
        if message.text:
            await bot.send_message(manager_id, message.text)

            await save_message(
                session=session,
                ticket_id=ticket.id,
                from_role=MessageRole.USER,
                message_type=MessageType.TEXT,
                telegram_message_id=message.message_id,
                text=message.text,
            )

        # === ФОТО ===
        elif message.photo:
            photo = message.photo[-1]
            await bot.send_photo(
                manager_id,
                photo.file_id,
                caption=message.caption
            )

            await save_message(
                session,
                ticket_id=ticket.id,
                from_role=MessageRole.USER,
                message_type=MessageType.PHOTO,
                telegram_message_id=message.message_id,
                caption=message.caption,
                file_id=photo.file_id,
            )

        # === ВИДЕО ===
        elif message.video:
            await bot.send_video(
                manager_id,
                message.video.file_id,
                caption=message.caption
            )

            await save_message(
                session,
                ticket_id=ticket.id,
                from_role=MessageRole.USER,
                message_type=MessageType.VIDEO,
                telegram_message_id=message.message_id,
                caption=message.caption,
                file_id=message.video.file_id,
            )

        # === VOICE ===
        elif message.voice:
            await bot.send_voice(
                manager_id,
                message.voice.file_id
            )

            await save_message(
                session,
                ticket_id=ticket.id,
                from_role=MessageRole.USER,
                message_type=MessageType.VOICE,
                telegram_message_id=message.message_id,
                file_id=message.voice.file_id,
            )

        # === STICKER ===
        elif message.sticker:
            await bot.send_sticker(
                manager_id,
                message.sticker.file_id
            )

            await save_message(
                session,
                ticket_id=ticket.id,
                from_role=MessageRole.USER,
                message_type=MessageType.STICKER,
                telegram_message_id=message.message_id,
                file_id=message.sticker.file_id,
            )