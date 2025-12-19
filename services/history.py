from sqlalchemy import select
from models import Message


async def get_ticket_history(session, ticket_id: int, limit=30):
    result = await session.execute(
        select(Message)
        .where(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return reversed(result.scalars().all())
