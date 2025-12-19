import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import engine
from models import Base
from handlers.user import router as user_router
from handlers.manager import router as manager_router
from handlers.manager_menu import router as manager_menu_router
from handlers.manager_history import router as manager_history_router
from handlers.manager_close import router as manager_close_router

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(manager_router)
dp.include_router(manager_menu_router)
dp.include_router(manager_history_router)
dp.include_router(manager_close_router)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
