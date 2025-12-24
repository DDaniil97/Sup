import asyncio
from aiogram import Bot, Dispatcher
from sqlalchemy import select

from config import BOT_TOKEN, SUPER_ADMIN, MANAGERS
from database import engine, SessionLocal
from models import Base, Manager

from handlers.user import router as user_router
from handlers.manager import router as manager_router
from handlers.manager_menu import router as manager_menu_router
from handlers.manager_history import router as manager_history_router
from handlers.manager_close import router as manager_close_router
from handlers.manager_callbacks import router as manager_callbacks_router
from handlers.admin import router as admin_router
from services.auto_close import auto_close_tickets
from handlers.close_ticket import router as close_ticket_router

async def bootstrap_managers():
    async with SessionLocal() as session:
        admin = await session.get(Manager, SUPER_ADMIN)

        if not admin:
            session.add(Manager(
                telegram_user_id=SUPER_ADMIN,
                is_admin=True,
                is_manager=True,
                is_active=True
            ))
        else:
            admin.is_admin = True
            admin.is_manager = True
            admin.is_active = True

        for manager_id in MANAGERS:
            if manager_id == SUPER_ADMIN:
                continue

            exists = await session.get(Manager, manager_id)
            if not exists:
                session.add(Manager(
                    telegram_user_id=manager_id,
                    is_admin=False,
                    is_manager=True,
                    is_active=True
                ))

        await session.commit()


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await bootstrap_managers()

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(manager_router)

    dp.include_router(manager_callbacks_router)
    dp.include_router(manager_menu_router)
    dp.include_router(manager_history_router)
    dp.include_router(manager_close_router)

    asyncio.create_task(auto_close_tickets(bot))
    dp.include_router(close_ticket_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
