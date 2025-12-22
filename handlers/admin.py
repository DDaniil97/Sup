from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal
from models import Manager

router = Router()


async def get_manager(session, user_id: int) -> Manager | None:
    return await session.get(Manager, user_id)


async def require_admin(message: Message) -> Manager | None:
    async with SessionLocal() as session:
        manager = await get_manager(session, message.from_user.id)

        if not manager or not manager.is_admin:
            await message.answer("🚫 Нет прав")
            return None

        return manager


@router.message(Command("add_manager"))
async def add_manager(message: Message):
    admin = await require_admin(message)
    if not admin:
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Использование: /add_manager <telegram_id>")

    manager_id = int(parts[1])

    async with SessionLocal() as session:
        # Нельзя менять владельца
        if manager_id == admin.telegram_user_id:
            return await message.answer("⚠️ Владелец уже имеет все права")

        manager = await session.get(Manager, manager_id)

        if manager:
            manager.is_manager = True
            manager.is_active = True
        else:
            session.add(Manager(
                telegram_user_id=manager_id,
                is_admin=False,
                is_manager=True,
                is_active=True
            ))

        await session.commit()

    await message.answer(f"✅ Менеджер {manager_id} добавлен")


@router.message(Command("remove_manager"))
async def remove_manager(message: Message):
    admin = await require_admin(message)
    if not admin:
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Использование: /remove_manager <telegram_id>")

    manager_id = int(parts[1])

    async with SessionLocal() as session:
        manager = await session.get(Manager, manager_id)

        if not manager:
            return await message.answer("❌ Менеджер не найден")

        if manager.is_admin:
            return await message.answer("❌ Нельзя удалить владельца")

        await session.delete(manager)
        await session.commit()

    await message.answer(f"🗑 Менеджер {manager_id} удалён")


@router.message(Command("list_managers"))
async def list_managers(message: Message):
    admin = await require_admin(message)
    if not admin:
        return

    async with SessionLocal() as session:
        result = await session.execute(select(Manager))
        managers = result.scalars().all()

    text = "👥 Менеджеры:\n\n"
    for m in managers:
        roles = []
        if m.is_admin:
            roles.append("admin")
        if m.is_manager:
            roles.append("manager")

        text += f"{m.telegram_user_id} — {', '.join(roles)}\n"

    await message.answer(text)

