from sqlalchemy.ext.asyncio import AsyncSession
from models import Message
from enums import MessageRole, MessageType


async def save_message(
    session: AsyncSession,
    ticket_id: int,
    from_role: MessageRole,
    message_type: MessageType,
    telegram_message_id: int,
    text: str | None = None,
    caption: str | None = None,
    file_id: str | None = None,
):
    msg = Message(
        ticket_id=ticket_id,
        from_role=from_role.value,
        message_type=message_type.value,
        telegram_message_id=telegram_message_id,
        text=text,
        caption=caption,
        file_id=file_id,
    )
    session.add(msg)
    await session.commit()
