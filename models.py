from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Boolean, Integer, Column, ForeignKey
from sqlalchemy.sql import func

from enums import TicketStatus, MessageRole, MessageType


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    username: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    first_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Manager(Base):
    __tablename__ = "managers"

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_telegram_id: Mapped[int] = mapped_column(BigInteger)

    status: Mapped[str] = mapped_column(
        String, default=TicketStatus.WAITING_MANAGER
    )

    assigned_manager_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    ticket_id: Mapped[int] = mapped_column(Integer)

    from_role: Mapped[str] = mapped_column(
        String
    )

    message_type: Mapped[str] = mapped_column(
        String
    )

    text: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    caption: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    telegram_message_id: Mapped[int] = mapped_column(
        BigInteger
    )

    file_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

class ManagerState(Base):
    __tablename__ = "manager_states"

    id = Column(Integer, primary_key=True)
    manager_telegram_id = Column(BigInteger, unique=True, index=True)
    active_ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
