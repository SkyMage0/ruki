"""Admin panel API and Jinja2 pages: cities, verification, disputes, users, stats."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import City, Task, User, VerificationRequest
from core.services.city_service import get_city_by_id, invalidate_cities_cache

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent.parent / "admin" / "templates")
)


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Dashboard: counts."""
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    tasks_count = (await db.execute(select(func.count(Task.id)))).scalar() or 0
    open_tasks = (
        await db.execute(select(func.count(Task.id)).where(Task.status == "open"))
    ).scalar() or 0
    pending_verification = (
        await db.execute(
            select(func.count(VerificationRequest.id)).where(
                VerificationRequest.status == "pending"
            )
        )
    ).scalar() or 0
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "users_count": users_count,
            "tasks_count": tasks_count,
            "open_tasks": open_tasks,
            "pending_verification": pending_verification,
        },
    )


@router.get("/cities", response_class=HTMLResponse)
async def admin_cities_list(request: Request, db: AsyncSession = Depends(get_db)):
    all_cities = (await db.execute(select(City).order_by(City.name))).scalars().all()
    return templates.TemplateResponse("cities.html", {"request": request, "cities": all_cities})


@router.post("/cities/add")
async def admin_city_add(
    request: Request,
    name: str = Form(...),
    timezone: str = Form("Europe/Moscow"),
    db: AsyncSession = Depends(get_db),
):
    city = City(name=name, timezone=timezone, is_active=True)
    db.add(city)
    await db.commit()
    await invalidate_cities_cache()
    return RedirectResponse(url="/admin/cities", status_code=303)


@router.post("/cities/{city_id}/toggle")
async def admin_city_toggle(city_id: int, db: AsyncSession = Depends(get_db)):
    city = await get_city_by_id(db, city_id)
    if not city:
        raise HTTPException(404, "City not found")
    city.is_active = not city.is_active
    await db.commit()
    await invalidate_cities_cache()
    return RedirectResponse(url="/admin/cities", status_code=303)


@router.get("/verification", response_class=HTMLResponse)
async def admin_verification_list(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VerificationRequest)
        .where(VerificationRequest.status == "pending")
        .order_by(VerificationRequest.created_at.desc())
    )
    requests_list = result.scalars().all()
    return templates.TemplateResponse(
        "verification.html", {"request": request, "requests": requests_list}
    )


@router.post("/verification/{req_id}/approve")
async def admin_verification_approve(req_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Request not found")
    req.status = "approved"
    user = (await db.execute(select(User).where(User.id == req.user_id))).scalar_one_or_none()
    if user:
        user.is_verified = True
    await db.commit()
    return RedirectResponse(url="/admin/verification", status_code=303)


@router.post("/verification/{req_id}/reject")
async def admin_verification_reject(req_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Request not found")
    req.status = "rejected"
    await db.commit()
    return RedirectResponse(url="/admin/verification", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def admin_users_search(
    request: Request,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    users = []
    if q:
        try:
            uid = int(q)
            result = await db.execute(
                select(User).where(or_(User.id == uid, User.telegram_id == uid))
            )
        except ValueError:
            result = await db.execute(select(User).where(User.full_name.ilike(f"%{q}%")))
        users = list(result.scalars().all())
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users, "q": q or ""}
    )


@router.get("/tasks", response_class=HTMLResponse)
async def admin_tasks_list(
    request: Request, status: str | None = None, db: AsyncSession = Depends(get_db)
):
    query = select(Task).order_by(Task.created_at.desc())
    if status:
        query = query.where(Task.status == status)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks})
