"""Inline keyboards for bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def cities_keyboard(cities):
    """List of cities as inline buttons."""
    rows = []
    for c in cities:
        rows.append([InlineKeyboardButton(c.name, callback_data=f"city:{c.id}")])
    return InlineKeyboardMarkup(rows)


def categories_keyboard():
    """Task categories."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Переезд / Грузчики", callback_data="cat:moving")],
        [InlineKeyboardButton("Уборка", callback_data="cat:cleaning")],
        [InlineKeyboardButton("Строительство / Ремонт", callback_data="cat:construction")],
        [InlineKeyboardButton("Погрузка / Разгрузка", callback_data="cat:loading")],
        [InlineKeyboardButton("Другое", callback_data="cat:other")],
    ])


def payment_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Почасовая (ставка/час за одного)", callback_data="pay:hourly")],
        [InlineKeyboardButton("Фиксированная (сумма одному)", callback_data="pay:fixed")],
    ])


def when_keyboard():
    """Когда нужен исполнитель: прямо сейчас или указать дату/время текстом."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Прямо сейчас", callback_data="when:now")],
    ])


def confirm_task_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Опубликовать", callback_data="task_confirm:yes")],
        [InlineKeyboardButton("Отмена", callback_data="task_confirm:no")],
    ])


def task_actions_keyboard(task_id: int, can_bid: bool = True):
    """For task view: Откликнуться."""
    buttons = []
    if can_bid:
        buttons.append([InlineKeyboardButton("Откликнуться", callback_data=f"bid:{task_id}")])
    return InlineKeyboardMarkup(buttons) if buttons else None


def bid_choice_keyboard(task_id: int):
    """Готов или Задать вопрос."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Готов", callback_data=f"bid_ready:{task_id}")],
        [InlineKeyboardButton("Задать вопрос", callback_data=f"bid_question:{task_id}")],
    ])


def question_reply_keyboard(task_id: int, worker_telegram_id: int):
    """Кнопка «Ответить» для заказчика на вопрос исполнителя (без принятия/отказа)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"question_reply:{task_id}:{worker_telegram_id}")],
    ])


def bid_decision_keyboard(bid_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Принять", callback_data=f"accept_bid:{bid_id}")],
        [InlineKeyboardButton("Отклонить", callback_data=f"reject_bid:{bid_id}")],
    ])


def my_tasks_tabs_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Как заказчик", callback_data="mytasks:customer"),
            InlineKeyboardButton("Как исполнитель", callback_data="mytasks:worker"),
        ],
    ])


def profile_keyboard():
    """Профиль: кнопка смены города."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Изменить город", callback_data="profile:change_city")],
    ])


def profile_cities_keyboard(cities):
    """Выбор города для профиля (callback_data: profile:city:ID)."""
    rows = [[InlineKeyboardButton(c.name, callback_data=f"profile:city:{c.id}")] for c in cities]
    return InlineKeyboardMarkup(rows)
