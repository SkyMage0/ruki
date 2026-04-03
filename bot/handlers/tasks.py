"""Task creation, list, my tasks, bid flow."""
import asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.monitoring import bot_commands_total, tasks_created_total, bids_total, get_logger
from core.rate_limit import check_create_task_limit, check_create_bid_limit
from core.services.user_service import get_user_by_telegram_id, create_user
from core.services.city_service import get_active_cities_cached
from core.services.task_service import (
    create_task,
    get_task_by_id,
    get_open_tasks_by_city,
    get_tasks_by_customer,
    get_tasks_where_worker_bidded,
    set_task_status,
)
from core.services.bid_service import (
    create_bid,
    get_bids_for_task,
    accept_bid,
    reject_bid,
    get_bid_by_id,
    count_accepted_bids_for_task,
)
from core.models import User
from core.models.task import TaskCategory, PaymentType
from core.models.bid import BidStatus
from core.models.user import UserRole
from core.redis_client import record_active_user

from bot.keyboards.inline import (
    cities_keyboard,
    categories_keyboard,
    payment_type_keyboard,
    confirm_task_keyboard,
    task_actions_keyboard,
    bid_decision_keyboard,
    bid_choice_keyboard,
    question_reply_keyboard,
    when_keyboard,
    my_tasks_tabs_keyboard,
    profile_keyboard,
    profile_cities_keyboard,
)

logger = get_logger()

# Conversation state keys
NEW_TASK_STEP = "new_task_step"
NEW_TASK_DATA = "new_task_data"


async def cmd_new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="new_task").inc()
    user = update.effective_user
    if not user:
        return
    await record_active_user(user.id)

    async with AsyncSessionLocal() as session:
        db_user = await get_user_by_telegram_id(session, user.id)
    if not db_user:
        await update.message.reply_text("Сначала пройдите регистрацию: /start")
        return

    # Только заказчик может создавать заказы
    if db_user.role != UserRole.customer.value:
        await update.message.reply_text(
            "Вы зарегистрированы как исполнитель.\n"
            "Создавать заказы могут только заказчики.\n"
            "Чтобы найти работу, используйте /tasks."
        )
        return

    if not db_user.city_id:
        await update.message.reply_text("Укажите город в профиле: /profile")
        return

    allowed, remaining = await check_create_task_limit(user.id)
    if not allowed:
        await update.message.reply_text(f"Лимит: 5 заказов в час. Попробуйте позже. (Осталось: {remaining})")
        return

    # Город берём из профиля пользователя, заново не спрашиваем
    context.user_data[NEW_TASK_STEP] = "category"
    context.user_data[NEW_TASK_DATA] = {"city_id": db_user.city_id}
    await update.message.reply_text("Выберите категорию:", reply_markup=categories_keyboard())


async def cmd_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="my_tasks").inc()
    user = update.effective_user
    if not user:
        return
    await record_active_user(user.id)

    async with AsyncSessionLocal() as session:
        db_user = await get_user_by_telegram_id(session, user.id)
        if not db_user:
            await update.message.reply_text("Сначала пройдите регистрацию: /start")
            return

        # Для заказчика показываем только заказы как заказчик.
        if db_user.role == UserRole.customer.value:
            tasks_list = await get_tasks_by_customer(session, db_user.id)
            if not tasks_list:
                await update.message.reply_text("У вас пока нет заказов как заказчик.")
                return
            await update.message.reply_text("Ваши заказы:")
            for t in tasks_list[:5]:
                await update.message.reply_text(_format_task_full(t))
            return

        # Для исполнителя — только отклики как исполнитель.
        if db_user.role == UserRole.worker.value:
            tasks_list = await get_tasks_where_worker_bidded(session, db_user.id)
            if not tasks_list:
                await update.message.reply_text("У вас пока нет откликов как исполнитель.")
                return
            await update.message.reply_text("Ваши отклики на заказы:")
            for t in tasks_list[:5]:
                await update.message.reply_text(_format_task_full(t))
            return


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="tasks").inc()
    user = update.effective_user
    if not user:
        return
    await record_active_user(user.id)

    async with AsyncSessionLocal() as session:
        db_user = await get_user_by_telegram_id(session, user.id)
    if not db_user:
        await update.message.reply_text("Сначала пройдите регистрацию: /start")
        return

    # Только исполнитель видит ленту задач
    if db_user.role != UserRole.worker.value:
        await update.message.reply_text(
            "Вы зарегистрированы как заказчик.\n"
            "Чтобы разместить заказ, используйте /new_task.\n"
            "Если вы хотите искать работу как исполнитель — обратитесь в поддержку для смены роли."
        )
        return
    if not db_user.city_id:
        await update.message.reply_text("Укажите город в профиле: /profile")
        return

    async with AsyncSessionLocal() as session:
        tasks_list = await get_open_tasks_by_city(session, db_user.city_id)
    if not tasks_list:
        await update.message.reply_text("В вашем городе пока нет открытых заказов.")
        return

    for t in tasks_list[:10]:
        # Читабельный текст оплаты
        if t.payment_type == "hourly":
            pay_text = f"Почасовая, ставка за одного: {t.payment_amount} ₽/час"
        else:
            pay_text = f"Фиксированная, сумма одному: {t.payment_amount} ₽"
        text = (
            f"#{t.id} {t.title}\n"
            f"Категория: {t.category}\n"
            f"Оплата: {pay_text}\n"
            f"Описание: {t.description[:200]}{'…' if len(t.description) > 200 else ''}"
        )
        kb = task_actions_keyboard(t.id, can_bid=True)
        await update.message.reply_text(text, reply_markup=kb)


def _format_task_full(t) -> str:
    workers = getattr(t, "workers_needed", 1)
    when_line = ""
    scheduled_at = getattr(t, "scheduled_at", None)
    is_urgent = getattr(t, "is_urgent", False)
    if scheduled_at:
        when_line = f"Когда: {scheduled_at.strftime('%d.%m %H:%M')}\n"
    elif is_urgent:
        when_line = "Когда: как можно скорее (СРОЧНО)\n"
    if t.payment_type == "hourly":
        pay_text = f"Почасовая, ставка за одного: {t.payment_amount} ₽/час"
    else:
        pay_text = f"Фиксированная, сумма одному: {t.payment_amount} ₽"
    text = (
        f"#{t.id} {t.title}\n"
        f"Описание: {t.description}\n"
        f"Адрес: {t.address_text}\n"
        f"Нужно исполнителей: {workers}\n"
        f"Оплата: {pay_text}\n"
        f"Статус: {t.status}"
    )
    if when_line:
        # Вставляем строку «Когда» перед количеством исполнителей
        text = (
            f"#{t.id} {t.title}\n"
            f"Описание: {t.description}\n"
            f"Адрес: {t.address_text}\n"
            f"{when_line}"
            f"Нужно исполнителей: {workers}\n"
            f"Оплата: {pay_text}\n"
            f"Статус: {t.status}"
        )
    return text


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    data = q.data
    user = update.effective_user
    if not user:
        return

    # Profile: change city
    if data == "profile:change_city":
        async with AsyncSessionLocal() as session:
            cities = await get_active_cities_cached(session)
        await q.edit_message_text("Выберите город:", reply_markup=profile_cities_keyboard(cities))
        return

    if data.startswith("profile:city:"):
        city_id = int(data.split(":")[2])
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            if not db_user:
                await q.edit_message_text("Ошибка: пользователь не найден.")
                return
            db_user.city_id = city_id
            await session.commit()
            cities = await get_active_cities_cached(session)
        city_name = next((c.name for c in cities if c.id == city_id), "не указан")
        from bot.handlers.profile import _profile_text
        text = _profile_text(db_user, city_name)
        await q.edit_message_text(text, reply_markup=profile_keyboard())
        return

    # Registration: city -> role -> create user
    if data.startswith("city:") and context.user_data.get("register_step") == "city":
        from bot.handlers.start import handle_role_choice
        city_id = int(data.split(":")[1])
        await handle_role_choice(update, context, city_id)
        return

    if data.startswith("role:"):
        role = data.split(":")[1]
        phone = context.user_data.get("phone")
        city_id = context.user_data.get("city_id")
        if phone is not None and city_id is not None:
            try:
                async with AsyncSessionLocal() as session:
                    usr = await create_user(
                        session, user.id, phone=phone, full_name=user.full_name or user.first_name,
                        role=role, city_id=city_id
                    )
                    await session.commit()
                context.user_data.clear()
                if role == UserRole.customer.value:
                    text = (
                        "Регистрация завершена!\n\n"
                        "Вы — заказчик."
                    )
                else:
                    text = (
                        "Регистрация завершена!\n\n"
                        "Вы — исполнитель."
                    )
                from bot.handlers.start import _main_menu_keyboard
                await q.edit_message_text(text, reply_markup=_main_menu_keyboard(role))
            except Exception as e:
                logger.exception("registration_failed", error=str(e))
                await q.edit_message_text("Ошибка регистрации. Попробуйте /start снова.")
        return

    # New task flow: category -> description -> address -> workers_needed -> payment -> confirm
    if data.startswith("cat:") and context.user_data.get(NEW_TASK_STEP) == "category":
        context.user_data[NEW_TASK_DATA]["category"] = data.split(":")[1]
        context.user_data[NEW_TASK_STEP] = "description"
        await q.edit_message_text("Введите описание заказа (текст):")
        return

    if data == "when:now" and context.user_data.get(NEW_TASK_STEP) == "when":
        # Срочный заказ: прямо сейчас
        context.user_data[NEW_TASK_DATA]["scheduled_at"] = None
        context.user_data[NEW_TASK_DATA]["is_urgent"] = True
        context.user_data[NEW_TASK_STEP] = "payment_type"
        await q.edit_message_text("Тип оплаты:", reply_markup=payment_type_keyboard())
        return

    if data.startswith("pay:") and context.user_data.get(NEW_TASK_STEP) == "payment_type":
        pay_type = data.split(":")[1]
        context.user_data[NEW_TASK_DATA]["payment_type"] = pay_type
        context.user_data[NEW_TASK_STEP] = "payment_amount"
        if pay_type == "hourly":
            await q.edit_message_text("Введите ставку за час за одного исполнителя (руб.):")
        else:
            await q.edit_message_text("Введите фиксированную сумму одному исполнителю (руб.):")
        return

    if data == "task_confirm:yes" and context.user_data.get(NEW_TASK_STEP) == "confirm":
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            if not db_user:
                await q.edit_message_text("Ошибка: пользователь не найден.")
                return
            d = context.user_data[NEW_TASK_DATA]
            task = await create_task(
                session,
                customer_id=db_user.id,
                title=d.get("title", "Заказ"),
                description=d.get("description", ""),
                category=d.get("category", "other"),
                city_id=d["city_id"],
                address_text=d.get("address_text", ""),
                payment_type=d.get("payment_type", "fixed"),
                payment_amount=int(d.get("payment_amount", 0)),
                workers_needed=int(d.get("workers_needed", 1)),
                scheduled_at=d.get("scheduled_at"),
                is_urgent=bool(d.get("is_urgent", False)),
            )
            city_name = "unknown"
            for c in (await get_active_cities_cached(session)):
                if c.id == d["city_id"]:
                    city_name = c.name
                    break
            await session.commit()
        tasks_created_total.labels(city=city_name).inc()
        logger.info("task_created", task_id=task.id, user_id=db_user.id, city=city_name)
        context.user_data.pop(NEW_TASK_STEP, None)
        context.user_data.pop(NEW_TASK_DATA, None)
        await q.edit_message_text(f"Заказ #{task.id} опубликован. Исполнители в вашем городе получат уведомление.")
        # Notify workers in city (non-blocking)
        async def notify_workers():
            async with AsyncSessionLocal() as s:
                r = await s.execute(
                    select(User.telegram_id).where(
                        User.city_id == d["city_id"],
                        User.telegram_id != user.id,
                        User.role == UserRole.worker.value,
                    )
                )
                tg_ids = [row[0] for row in r.all()]
            msg = f"Новый заказ #{task.id}: {d.get('title', 'Заказ')[:50]}. Оплата: {d.get('payment_amount')} ({d.get('payment_type')}). /tasks"
            for tid in tg_ids:
                try:
                    await context.bot.send_message(chat_id=tid, text=msg)
                except Exception as e:
                    logger.info("bot_notify_error", error=str(e))
        asyncio.create_task(notify_workers())
        return

    if data == "task_confirm:no":
        context.user_data.pop(NEW_TASK_STEP, None)
        context.user_data.pop(NEW_TASK_DATA, None)
        await q.edit_message_text("Создание заказа отменено.")
        return

    # Bid: показать заказ и кнопки «Готов» / «Задать вопрос»
    if data.startswith("bid:"):
        task_id = int(data.split(":")[1])
        allowed, _ = await check_create_bid_limit(user.id)
        if not allowed:
            await q.edit_message_text("Лимит откликов: 20 в час. Попробуйте позже.")
            return
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            task = await get_task_by_id(session, task_id)
            if task:
                accepted = await count_accepted_bids_for_task(session, task_id)
                if accepted >= getattr(task, "workers_needed", 1):
                    task = None
        if not db_user or not task or task.status != "open":
            await q.edit_message_text("Заказ недоступен или набор исполнителей уже закрыт.")
            return
        await q.edit_message_text(
            _format_task_full(task) + "\n\nВыберите действие:",
            reply_markup=bid_choice_keyboard(task_id),
        )
        return

    # Готов — отправить отклик «Готов»
    if data.startswith("bid_ready:"):
        task_id = int(data.split(":")[1])
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            task = await get_task_by_id(session, task_id)
            if task:
                accepted = await count_accepted_bids_for_task(session, task_id)
                if accepted >= getattr(task, "workers_needed", 1):
                    task = None
        if not db_user or not task or task.status != "open":
            await q.edit_message_text("Заказ недоступен или набор исполнителей уже закрыт.")
            return
        async with AsyncSessionLocal() as session:
            bid = await create_bid(session, task_id=task_id, worker_id=db_user.id, message="Готов")
            if not bid:
                await q.edit_message_text("Вы уже откликались на этот заказ.")
                return
            task = await get_task_by_id(session, task_id)
            await session.commit()
        bids_total.inc()
        await q.edit_message_text("Отклик «Готов» отправлен. Ожидайте решения заказчика.")
        try:
            rating_str = f"Рейтинг исполнителя: {db_user.rating:.1f}. "
            await context.bot.send_message(
                chat_id=task.customer.telegram_id,
                text=f"Новый отклик на заказ #{task_id}. {rating_str}Сообщение: Готов.",
                reply_markup=bid_decision_keyboard(bid.id),
            )
        except Exception as e:
            logger.info("bot_notify_error", error=str(e))
        return

    # Задать вопрос — запросить текст вопроса
    if data.startswith("bid_question:"):
        task_id = int(data.split(":")[1])
        async with AsyncSessionLocal() as session:
            task = await get_task_by_id(session, task_id)
            if task:
                accepted = await count_accepted_bids_for_task(session, task_id)
                if accepted >= getattr(task, "workers_needed", 1):
                    task = None
        if not task or task.status != "open":
            await q.edit_message_text("Заказ недоступен или набор исполнителей уже закрыт.")
            return
        context.user_data["pending_question_task_id"] = task_id
        await q.edit_message_text("Напишите ваш вопрос заказчику (текстом):")
        return

    # Заказчик нажал «Ответить» на вопрос исполнителя
    if data.startswith("question_reply:"):
        parts = data.split(":")
        if len(parts) >= 3:
            task_id = int(parts[1])
            worker_telegram_id = int(parts[2])
            context.user_data["pending_question_reply"] = (task_id, worker_telegram_id)
            await q.edit_message_text("Напишите ответ исполнителю (текстом):")
        return

    # Accept / Reject bid (customer)
    if data.startswith("accept_bid:"):
        bid_id = int(data.split(":")[1])
        from core.services.user_service import get_phone_decrypted, get_user_by_id
        from core.models.task import Task

        async with AsyncSessionLocal() as session:
            bid = await accept_bid(session, bid_id)
            if not bid:
                await q.edit_message_text("Отклик уже обработан.")
                return

            # Берём id исполнителя и задачи из заявки
            worker_id = bid.worker_id
            task_id = bid.task_id

            # Находим id заказчика по задаче
            res = await session.execute(select(Task.customer_id).where(Task.id == task_id))
            customer_id = res.scalar_one_or_none()

            worker = await get_user_by_id(session, worker_id)
            customer = await get_user_by_id(session, customer_id) if customer_id is not None else None

            worker_phone = get_phone_decrypted(worker) if worker else None
            customer_phone = get_phone_decrypted(customer) if customer else None
            worker_telegram_id = worker.telegram_id if worker else None
            worker_rating = worker.rating if worker else 0.0

            await session.commit()

        await q.edit_message_text(
            f"Вы приняли отклик.\n"
            f"Исполнитель рейтинг: {worker_rating:.1f}.\n"
            f"Контакт исполнителя: {worker_phone or 'не указан'}.\n"
            f"Исполнителю отправлен ваш контакт."
        )
        if worker_telegram_id:
            try:
                await context.bot.send_message(
                    chat_id=worker_telegram_id,
                    text=f"Ваш отклик принят! Контакт заказчика: {customer_phone or 'не указан'}",
                )
            except Exception as e:
                logger.info("bot_notify_error", error=str(e))
        return

    if data.startswith("reject_bid:"):
        bid_id = int(data.split(":")[1])
        async with AsyncSessionLocal() as session:
            bid = await reject_bid(session, bid_id)
            await session.commit()
        await q.edit_message_text("Отклик отклонён.")
        return

    # My tasks tabs
    if data == "mytasks:customer":
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            tasks_list = await get_tasks_by_customer(session, db_user.id) if db_user else []
        if not tasks_list:
            await q.edit_message_text("У вас пока нет заказов как заказчик.")
        else:
            for t in tasks_list[:5]:
                await q.message.reply_text(_format_task_full(t))
        return

    if data == "mytasks:worker":
        async with AsyncSessionLocal() as session:
            db_user = await get_user_by_telegram_id(session, user.id)
            tasks_list = await get_tasks_where_worker_bidded(session, db_user.id) if db_user else []
        if not tasks_list:
            await q.edit_message_text("У вас пока нет откликов как исполнитель.")
        else:
            for t in tasks_list[:5]:
                await q.message.reply_text(_format_task_full(t))
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Conversation: new_task text steps and bid message."""
    text = (update.message and update.message.text) or ""
    user = update.effective_user
    if not user:
        return

    step = context.user_data.get(NEW_TASK_STEP)
    if step == "description":
        context.user_data[NEW_TASK_DATA]["description"] = text
        context.user_data[NEW_TASK_DATA]["title"] = text[:100] if len(text) > 100 else text
        context.user_data[NEW_TASK_STEP] = "address"
        await update.message.reply_text("Введите адрес (текстом):")
        return

    if step == "address":
        context.user_data[NEW_TASK_DATA]["address_text"] = text[:500]
        context.user_data[NEW_TASK_STEP] = "workers_needed"
        await update.message.reply_text("Сколько исполнителей нужно? Введите число (например, 1 или 2).")
        return

    if step == "workers_needed":
        try:
            count = int(text.strip())
            if count <= 0:
                raise ValueError("positive")
        except ValueError:
            await update.message.reply_text("Введите целое положительное число (количество исполнителей).")
            return
        context.user_data[NEW_TASK_DATA]["workers_needed"] = count
        context.user_data[NEW_TASK_STEP] = "when"
        await update.message.reply_text(
            "На когда нужен исполнитель?\n"
            "Введите дату и время в формате ДД.ММ ЧЧ:ММ (например, 14.03 18:00),\n"
            "или нажмите «Прямо сейчас».",
            reply_markup=when_keyboard(),
        )
        return

    if step == "when":
        from datetime import datetime as _dt
        text_clean = text.strip()
        try:
            scheduled = _dt.strptime(text_clean, "%d.%m %H:%M")
        except ValueError:
            await update.message.reply_text(
                "Не понял дату и время.\n"
                "Введите в формате ДД.ММ ЧЧ:ММ, например: 14.03 18:00,\n"
                "или нажмите кнопку «Прямо сейчас»."
            )
            return
        context.user_data[NEW_TASK_DATA]["scheduled_at"] = scheduled
        context.user_data[NEW_TASK_DATA]["is_urgent"] = False
        context.user_data[NEW_TASK_STEP] = "payment_type"
        await update.message.reply_text("Тип оплаты:", reply_markup=payment_type_keyboard())
        return

    if step == "payment_amount":
        try:
            amount = int(text.strip())
            if amount <= 0:
                raise ValueError("positive")
        except ValueError:
            await update.message.reply_text("Введите целое положительное число.")
            return
        context.user_data[NEW_TASK_DATA]["payment_amount"] = amount
        context.user_data[NEW_TASK_STEP] = "confirm"
        d = context.user_data[NEW_TASK_DATA]
        when_line = ""
        scheduled_at = d.get("scheduled_at")
        is_urgent = d.get("is_urgent", False)
        if scheduled_at:
            when_line = f"Когда: {scheduled_at.strftime('%d.%m %H:%M')}\n"
        elif is_urgent:
            when_line = "Когда: как можно скорее (СРОЧНО)\n"
        # Читаемый текст типа оплаты
        pay_type = d.get("payment_type")
        if pay_type == "hourly":
            pay_text = f"Почасовая, ставка за одного: {d['payment_amount']} ₽/час"
        else:
            pay_text = f"Фиксированная, сумма одному: {d['payment_amount']} ₽"

        summary = (
            f"Проверьте:\nКатегория: {d['category']}\n"
            f"Описание: {d['description'][:200]}...\nАдрес: {d['address_text']}\n"
        )
        if when_line:
            summary += when_line
        summary += (
            f"Нужно исполнителей: {d.get('workers_needed', 1)}\n"
            f"Оплата: {pay_text}"
        )
        await update.message.reply_text(summary, reply_markup=confirm_task_keyboard())
        return

    # Вопрос исполнителя заказчику (после нажатия «Задать вопрос»).
    # Вопрос сам по себе не создаёт заявку «готов», это просто общение.
    task_id = context.user_data.get("pending_question_task_id")
    if task_id is not None:
        context.user_data.pop("pending_question_task_id", None)
        async with AsyncSessionLocal() as session:
            task = await get_task_by_id(session, task_id)
            customer_telegram_id = task.customer.telegram_id if task and task.customer else None
        if not task or not customer_telegram_id:
            await update.message.reply_text("Заказ не найден.")
            return
        await update.message.reply_text("Вопрос отправлен заказчику. Ожидайте ответа.")
        try:
            await context.bot.send_message(
                chat_id=customer_telegram_id,
                text=f"Вопрос по заказу #{task_id} от исполнителя:\n\n{text}",
                reply_markup=question_reply_keyboard(task_id, user.id),
            )
        except Exception as e:
            logger.info("bot_notify_error", error=str(e))
        return

    # Ответ заказчика исполнителю (после нажатия «Ответить» на вопрос)
    reply_state = context.user_data.get("pending_question_reply")
    if reply_state is not None:
        context.user_data.pop("pending_question_reply", None)
        task_id, worker_telegram_id = reply_state
        await update.message.reply_text("Ответ отправлен исполнителю.")
        try:
            await context.bot.send_message(
                chat_id=worker_telegram_id,
                text=f"Ответ заказчика по заказу #{task_id}:\n\n{text}",
            )
        except Exception as e:
            logger.info("bot_notify_error", error=str(e))
        return
