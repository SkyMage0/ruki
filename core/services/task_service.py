"""Task CRUD and listing."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Bid, Task
from core.models.bid import BidStatus
from core.models.task import TaskStatus


async def create_task(
    session: AsyncSession,
    customer_id: int,
    title: str,
    description: str,
    category: str,
    city_id: int,
    address_text: str,
    payment_type: str,
    payment_amount: int,
    workers_needed: int = 1,
    scheduled_at: datetime | None = None,
    is_urgent: bool = False,
) -> Task:
    task = Task(
        customer_id=customer_id,
        title=title,
        description=description,
        category=category,
        city_id=city_id,
        address_text=address_text,
        payment_type=payment_type,
        payment_amount=payment_amount,
        workers_needed=workers_needed,
        status=TaskStatus.open.value,
        scheduled_at=scheduled_at,
        is_urgent=is_urgent,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def get_task_by_id(session: AsyncSession, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.customer), selectinload(Task.city))
    )
    return result.scalar_one_or_none()


async def get_open_tasks_by_city(
    session: AsyncSession, city_id: int, limit: int = 50
) -> list[Task]:
    """Открытые заказы по городу, у которых ещё не набрано workers_needed исполнителей."""
    accepted_count = (
        select(func.count(Bid.id))
        .where(Bid.task_id == Task.id, Bid.status == BidStatus.accepted.value)
        .scalar_subquery()
    )
    result = await session.execute(
        select(Task)
        .where(
            Task.city_id == city_id,
            Task.status == TaskStatus.open.value,
            accepted_count < Task.workers_needed,
        )
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_tasks_by_customer(session: AsyncSession, customer_id: int) -> list[Task]:
    result = await session.execute(
        select(Task).where(Task.customer_id == customer_id).order_by(Task.created_at.desc())
    )
    return list(result.scalars().all())


async def get_tasks_where_worker_bidded(session: AsyncSession, worker_id: int) -> list[Task]:
    result = await session.execute(
        select(Task)
        .join(Bid, Bid.task_id == Task.id)
        .where(Bid.worker_id == worker_id)
        .order_by(Task.created_at.desc())
    )
    return list(result.unique().scalars().all())


async def set_task_status(session: AsyncSession, task_id: int, status: str) -> Task | None:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        task.status = status
        if status == TaskStatus.completed.value:
            task.completed_at = datetime.utcnow()
        await session.flush()
        await session.refresh(task)
    return task
