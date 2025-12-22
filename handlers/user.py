from aiogram import Router, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram import F
from sqlalchemy import select

from database import SessionLocal
from enums import TicketStatus
from models import Ticket, User, Manager
from services.notify import notify_managers
from models import Message as TicketMessage

router = Router()

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✍️ Написать обращение")]],
    resize_keyboard=True
)


@router.message(CommandStart())
async def user_start(message: Message):
    async with SessionLocal() as session:
        # 🔹 ЕСЛИ ЭТО МЕНЕДЖЕР — НЕ ПОКАЗЫВАЕМ КНОПКУ
        manager = await session.get(Manager, message.from_user.id)
        if manager and manager.is_manager and manager.is_active:
            await message.answer(
                "🧑‍💼 Вы менеджер поддержки\n\n"
                "Используйте команду /dialogs для работы с обращениями"
            )
            return

        # 🔹 ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            session.add(user)
            await session.commit()

    await message.answer(
        "👋 Добро пожаловать в поддержку!\n"
        "Нажмите кнопку ниже, чтобы написать обращение.",
        reply_markup=user_keyboard
    )

@router.message(
    F.content_type.in_({"text", "photo", "video", "voice"}) &
    ~F.text.startswith("/")
)
async def user_message_handler(message: Message, bot: Bot):
    async with SessionLocal() as session:
        # Проверяем, является ли отправитель менеджером
        manager = await session.get(Manager, message.from_user.id)
        if manager and manager.is_manager and manager.is_active:
            # Менеджер пишет — логика не меняется
            result = await session.execute(
                select(Ticket)
                .where(Ticket.assigned_manager_telegram_id == message.from_user.id)
                .order_by(Ticket.created_at.desc())
                .limit(1)
            )
            ticket = result.scalar_one_or_none()
            if not ticket:
                await message.answer("❌ Нет активного тикета для ответа")
                return

            msg_record = TicketMessage(
                ticket_id=ticket.id,
                from_role="manager",
                message_type=message.content_type,
                text=message.text,
                telegram_message_id=message.message_id
            )
            session.add(msg_record)
            await session.commit()

            await bot.send_message(
                chat_id=ticket.user_telegram_id,
                text=f"🧑‍💻 Менеджер:\n{message.text}"
            )
            await message.answer("✅ Сообщение отправлено пользователю")
            return

        # Обычный пользователь
        result = await session.execute(
            select(Ticket)
            .where(
                Ticket.user_telegram_id == message.from_user.id,
                Ticket.status.in_([
                    TicketStatus.WAITING_MANAGER,
                    TicketStatus.ASSIGNED
                ])
            )
            .order_by(Ticket.created_at.desc())
            .limit(1)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            # Нет текущего тикета — создаём новый
            ticket = Ticket(
                user_telegram_id=message.from_user.id,
                status=TicketStatus.WAITING_MANAGER
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)

        # Сохраняем сообщение пользователя
        msg_record = TicketMessage(
            ticket_id=ticket.id,
            from_role="user",
            message_type=message.content_type,
            text=message.text,
            telegram_message_id=message.message_id
        )
        session.add(msg_record)
        await session.commit()

        # Отправляем уведомление только тем менеджерам, кто ведёт тикет
        if ticket.assigned_manager_telegram_id:
            # Тикет уже взят менеджером — отправляем только ему
            await bot.send_message(
                chat_id=ticket.assigned_manager_telegram_id,
                text=f"👤 Пользователь:\n{message.text}"
            )
        else:
            # Тикет еще не взят — уведомляем всех менеджеров
            user_info = (
                f"👤 {message.from_user.first_name}\n"
                f"@{message.from_user.username}\n"
                f"ID: {message.from_user.id}"
            )
            await notify_managers(
                bot=bot,
                session=session,
                ticket_id=ticket.id,
                user_info=user_info
            )

    await message.answer("✅ Сообщение отправлено в поддержку")
