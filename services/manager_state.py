from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ManagerState


async def get_manager_state(
    session: AsyncSession,
    manager_id: int
) -> ManagerState:
    result = await session.execute(
        select(ManagerState)
        .where(ManagerState.manager_telegram_id == manager_id)
    )
    state = result.scalar_one_or_none()

    if not state:
        state = ManagerState(
            manager_telegram_id=manager_id,
            active_ticket_id=None
        )
        session.add(state)
        await session.commit()   # 🔥 ОБЯЗАТЕЛЬНО
        await session.refresh(state)

    return state


async def set_active_ticket(
    session: AsyncSession,
    manager_id: int,
    ticket_id: int
):
    state = await get_manager_state(session, manager_id)
    state.active_ticket_id = ticket_id

    await session.commit()      # 🔥 ВОТ ЭТОГО НЕ ХВАТАЛО

