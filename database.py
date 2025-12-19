from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from config import DB_URL

# Async engine
engine = create_async_engine(
    DB_URL,
    echo=False,        # поставь True для отладки SQL
    pool_pre_ping=True
)

# Фабрика сессий
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
