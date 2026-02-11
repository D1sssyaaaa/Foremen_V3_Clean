"""Клавиатуры для Telegram бота"""
from datetime import datetime, timedelta
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


from app.core.config import settings

def get_main_menu_keyboard(role: str = None) -> ReplyKeyboardMarkup:
    """Главное меню бота с учетом роли"""
    builder = ReplyKeyboardBuilder()
    
    # URL для Mini Apps (предполагаем, что они настроены)
    # Используем settings.miniapp_url, который должен указывать на GitHub Pages
    web_app_timesheet = WebAppInfo(url=f"{settings.miniapp_url}/miniapp/timesheets")
    web_app_materials = WebAppInfo(url=f"{settings.miniapp_url}/miniapp/material-request/select-object") # Предполагаем такой роут или /objects
    # Для материалов лучше открыть выбор объекта. Текущий роут /miniapp/objects
    web_app_objects = WebAppInfo(url=f"{settings.miniapp_url}/miniapp/objects")
    web_app_manager = WebAppInfo(url=f"{settings.miniapp_url}/miniapp/manager")
    
    # 1. Бригадир (FOREMAN)
    if role == "FOREMAN":
        builder.row(
            KeyboardButton(text="📝 Табель", web_app=web_app_timesheet),
            KeyboardButton(text="📦 Заказать материал", web_app=web_app_objects)
        )
        builder.row(
            KeyboardButton(text="🚜 Заказать технику"), # Оставляем текстом/формой
            KeyboardButton(text="📈 Мои заявки")
        )
        
    # 2. Менеджер по снабжению (MATERIALS_MANAGER)
    elif role == "MATERIALS_MANAGER":
        builder.row(
            KeyboardButton(text="📋 Активные заявки"), # Список заявок текстом/инлайн
            KeyboardButton(text="🚚 Отгрузки")
        )
        builder.row(
            KeyboardButton(text="📊 Архив заявок")
        )
        
    # 3. Менеджер по технике (EQUIPMENT_MANAGER)
    elif role == "EQUIPMENT_MANAGER":
        builder.row(
            KeyboardButton(text="🚜 График техники"), # Можно Mini App или текст
            KeyboardButton(text="📋 Новые заявки")
        )
        builder.row(
            KeyboardButton(text="✅ Активная техника")
        )
        
    # 4. Руководитель (HEAD / ADMIN)
    elif role in ["HEAD", "ADMIN", "MANAGER"]: # MANAGER теперь как Руководитель
        builder.row(
            KeyboardButton(text="📊 Панель руководителя", web_app=web_app_manager)
        )
        builder.row(
            KeyboardButton(text="🏗 Объекты") # Список объектов текстом?
        )
        # Если Админ, добавим функционал всех
        if role == "ADMIN":
             builder.row(
                KeyboardButton(text="🛠 Админ панель"),
                KeyboardButton(text="🔄 Сменить роль") # Для тестов
            )

    # Базовое (Гость)
    else:
        builder.row(
            KeyboardButton(text="📝 Регистрация")
        )

    builder.row(
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_material_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа материала"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏗️ Обычные материалы", callback_data="mattype:regular"),
        InlineKeyboardButton(text="🪨 Инертные материалы", callback_data="mattype:inert")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_urgency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора срочности"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 Обычная", callback_data="urgency:normal"),
        InlineKeyboardButton(text="🟡 Срочная", callback_data="urgency:urgent"),
        InlineKeyboardButton(text="🔴 Критичная", callback_data="urgency:critical")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")
    )
    return builder.as_markup()


def get_add_more_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура добавления дополнительных позиций"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить еще", callback_data="add:more"),
        InlineKeyboardButton(text="✅ Завершить", callback_data="add:done")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_equipment_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа техники"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏗️ Экскаватор", callback_data="eqtype:excavator"),
        InlineKeyboardButton(text="🏗️ Кран", callback_data="eqtype:crane")
    )
    builder.row(
        InlineKeyboardButton(text="🚜 Бульдозер", callback_data="eqtype:bulldozer"),
        InlineKeyboardButton(text="🚚 Погрузчик", callback_data="eqtype:loader")
    )
    builder.row(
        InlineKeyboardButton(text="🥤 Бетономешалка", callback_data="eqtype:mixer"),
        InlineKeyboardButton(text="🔧 Другое", callback_data="eqtype:other")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="no")
    )
    return builder.as_markup()


def get_objects_keyboard(objects: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора объекта учета"""
    builder = InlineKeyboardBuilder()
    
    for obj in objects:
        # Формируем кнопку: код - название
        text = f"{obj.get('code', 'N/A')} - {obj.get('name', 'Без названия')[:30]}"
        callback_data = f"object:{obj['id']}"
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()



def get_register_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для начала регистрации"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="register_start")
    )
    return builder.as_markup()


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли при регистрации"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👷 Бригадир", callback_data="role:FOREMAN"))
    builder.row(InlineKeyboardButton(text="🚜 Менеджер по технике", callback_data="role:EQUIPMENT_MANAGER"))
    builder.row(InlineKeyboardButton(text="📦 Менеджер по снабжению", callback_data="role:MATERIALS_MANAGER"))
    builder.row(InlineKeyboardButton(text="💰 Бухгалтер", callback_data="role:ACCOUNTANT"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration"))
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропуска"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")
    )
    return builder.as_markup()


def get_confirm_registration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения регистрации"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_registration"),
        InlineKeyboardButton(text="🔄 Заново", callback_data="restart_registration")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")
    )
    return builder.as_markup()


def get_date_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора даты поставки (сегодня + 7 дней)"""
    builder = InlineKeyboardBuilder()
    today = datetime.now().date()
    
    # Названия дней недели
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    # Первый ряд: сегодня, завтра, послезавтра
    for i in range(3):
        date = today + timedelta(days=i)
        weekday = weekdays[date.weekday()]
        if i == 0:
            text = f"📅 Сегодня ({date.strftime('%d.%m')})"
        elif i == 1:
            text = f"📅 Завтра ({date.strftime('%d.%m')})"
        else:
            text = f"📅 {weekday} {date.strftime('%d.%m')}"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"date:{date.isoformat()}"))
    
    # Второй блок: +3 до +7 дней (по 2 в ряд)
    row_buttons = []
    for i in range(3, 8):
        date = today + timedelta(days=i)
        weekday = weekdays[date.weekday()]
        text = f"{weekday} {date.strftime('%d.%m')}"
        row_buttons.append(InlineKeyboardButton(text=text, callback_data=f"date:{date.isoformat()}"))
        if len(row_buttons) == 2:
            builder.row(*row_buttons)
            row_buttons = []
    if row_buttons:
        builder.row(*row_buttons)
    
    # Кнопка ввода другой даты
    builder.row(InlineKeyboardButton(text="📝 Другая дата", callback_data="date:custom"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_skip_comment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропуска комментария"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭️ Без комментария", callback_data="skip_comment")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()

















def get_manager_dashboard_keyboard(url: str) -> InlineKeyboardMarkup:
    """Клавиатура для открытия панели руководителя"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Открыть панель руководителя", web_app=WebAppInfo(url=url))
    )
    return builder.as_markup()
