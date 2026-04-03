"""Bid CRUD and accept/reject."""
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Bid, Task
from core.models.bid import BidStatus
from core.models.task import TaskStatus


async def count_accepted_bids_for_task(session: AsyncSession, task_id: int) -> int:
    """Количество принятых откликов по задаче."""
    r = await session.execute(
        select(func.count(Bid.id)).where(
            Bid.task_id == task_id,
            Bid.status == BidStatus.accepted.value,
        )
    )
    return r.scalar() or 0


async def create_bid(
    session: AsyncSession,
    task_id: int,
    worker_id: int,
    message: Optional[str] = None,
    proposed_amount: Optional[int] = None,
) -> Optional[Bid]:
    # Check unique (task_id, worker_id)
    existing = await session.execute(
        select(Bid).where(Bid.task_id == task_id, Bid.worker_id == worker_id)
    )
    if existing.scalar_one_or_none():
        return None
    bid = Bid(
        task_id=task_id,
        worker_id=worker_id,
        message=message,
        proposed_amount=proposed_amount,
        status=BidStatus.pending.value,
    )
    session.add(bid)
    await session.flush()
    await session.refresh(bid)
    return bid


async def get_bids_for_task(session: AsyncSession, task_id: int) -> List[Bid]:
    result = await session.execute(
        select(Bid).where(Bid.task_id == task_id).options(selectinload(Bid.worker))
    )
    return list(result.scalars().all())


async def accept_bid(session: AsyncSession, bid_id: int) -> Optional[Bid]:
    """Принять отклик. Если набрано workers_needed — задача закрыта для новых, остальные отклики отклоняем."""
    result = await session.execute(
        select(Bid)
        .where(Bid.id == bid_id)
        .options(
            selectinload(Bid.worker),
            selectinload(Bid.task).selectinload(Task.customer),
        )
    )
    bid = result.scalar_one_or_none()
    if not bid or bid.status != BidStatus.pending.value:
        return None
    bid.status = BidStatus.accepted.value
    await session.flush()
    accepted_count = await count_accepted_bids_for_task(session, bid.task_id)
    workers_needed = getattr(bid.task, "workers_needed", 1)
    if accepted_count >= workers_needed:
        bid.task.status = TaskStatus.in_progress.value
        # Закрываем набор: отклоняем все оставшиеся pending
        await session.execute(
            update(Bid).where(
                Bid.task_id == bid.task_id,
                Bid.id != bid.id,
                Bid.status == BidStatus.pending.value,
            ).values(status=BidStatus.rejected.value)
        )
    await session.flush()
    await session.refresh(bid)
    return bid


async def reject_bid(session: AsyncSession, bid_id: int) -> Optional[Bid]:
    result = await session.execute(select(Bid).where(Bid.id == bid_id))
    bid = result.scalar_one_or_none()
    if not bid or bid.status != BidStatus.pending.value:
        return None
    bid.status = BidStatus.rejected.value
    await session.flush()
    await session.refresh(bid)
    return bid


async def get_bid_by_id(session: AsyncSession, bid_id: int) -> Optional[Bid]:
    result = await session.execute(
        select(Bid).where(Bid.id == bid_id).options(selectinload(Bid.task), selectinload(Bid.worker))
    )
    return result.scalar_one_or_none()
