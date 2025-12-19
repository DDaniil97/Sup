from sqlalchemy import select
from models import ManagerState


async def get_manager_state(session, manager_id: int):
    result = await session.execute(
        select(ManagerState).where(
            ManagerState.manager_telegram_id == manager_id
        )
    )
    state = result.scalar_one_or_none()

    if not state:
        state = ManagerState(manager_telegram_id=manager_id)
        session.add(state)
        await session.commit()

    return state


async def set_active_ticket(session, manager_id: int, ticket_id: int | None):
    state = await get_manager_state(session, manager_id)
    state.active_ticket_id = ticket_id
    await session.commit()
