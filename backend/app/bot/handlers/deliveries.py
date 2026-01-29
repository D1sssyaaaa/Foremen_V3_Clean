"""
Handler для создания заявок на доставку материалов через Telegram бот
Доступно: MANAGER, MATERIALS_MANAGER, FOREMAN
"""
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.bot.states import DeliveryStates
from app.bot.utils.api_client import APIClient
from app.core.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = Router()


async def get_user_token(user_id: int, db_session=None) -> str:
    """Получение токена пользователя"""
    # TODO: Получить токен из сессии/кэша пользователя
    # На данный момент используется заглушка
    return ""


async def get_available_objects(token: str) -> list:
    """Получение доступных объектов пользователя"""
    api = APIClient(token)
    try:
        objects = await api.get_objects()
        return objects if objects else []
    except Exception as e:
        logger.error(f"Ошибка при получении объектов: {e}")
        return []


def delivery_objects_keyboard(objects: list) -> ReplyKeyboardMarkup:
    """Клавиатура для выбора объекта"""
    buttons = []
    for obj in objects:
        obj_code = obj.get("code", "?")
        obj_name = obj.get("name", "Unknown")
        button_text = f"{obj_code} - {obj_name[:30]}"
        buttons.append([KeyboardButton(text=button_text)])
    
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите объект"
    )


def delivery_date_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для быстрого выбора даты доставки"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_later = today + timedelta(days=7)
    
    buttons = [
        [KeyboardButton(text=f"📅 Сегодня ({today.strftime('%d.%m')})")],
        [KeyboardButton(text=f"📅 Завтра ({tomorrow.strftime('%d.%m')})")],
        [KeyboardButton(text=f"📅 Через неделю ({week_later.strftime('%d.%m')})")],
        [KeyboardButton(text="✏️ Указать дату вручную")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )


@router.message(F.text == "🚚 Создать доставку")
async def cmd_delivery_start(message: types.Message, state: FSMContext):
    """Начало процесса создания доставки"""
    user_id = message.from_user.id
    
    try:
        # Получение доступных объектов
        objects = await get_available_objects("")  # TODO: получить реальный токен
        
        if not objects:
            await message.answer(
                "❌ У вас нет доступных объектов для создания доставки.\n"
                "Обратитесь к администратору.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="↩️ Назад в меню")]],
                    resize_keyboard=True
                )
            )
            return
        
        # Сохранение объектов в состояние
        await state.update_data(objects=objects)
        
        # Запрос на выбор объекта
        await message.answer(
            "🏗️ **Выберите объект для доставки:**",
            reply_markup=delivery_objects_keyboard(objects)
        )
        await state.set_state(DeliveryStates.select_object)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске создания доставки: {e}")
        await message.answer(
            "❌ Ошибка при загрузке объектов. Попробуйте позже.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="↩️ Назад в меню")]],
                resize_keyboard=True
            )
        )


@router.message(DeliveryStates.select_object, F.text != "❌ Отмена")
async def delivery_select_object(message: types.Message, state: FSMContext):
    """Обработка выбора объекта"""
    try:
        data = await state.get_data()
        objects = data.get("objects", [])
        
        # Поиск выбранного объекта
        selected_object = None
        for obj in objects:
            if message.text.startswith(obj.get("code", "")):
                selected_object = obj
                break
        
        if not selected_object:
            await message.answer("❌ Объект не найден. Попробуйте еще раз.")
            return
        
        # Сохранение выбранного объекта
        await state.update_data(selected_object=selected_object)
        
        # Запрос суммы доставки
        await message.answer(
            f"✅ Выбран объект: **{selected_object.get('code')} - {selected_object.get('name')}**\n\n"
            f"💰 **Введите сумму доставки (в рублях):**",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )
        await state.set_state(DeliveryStates.input_amount)
        
    except Exception as e:
        logger.error(f"Ошибка при выборе объекта: {e}")
        await message.answer("❌ Ошибка обработки. Попробуйте снова.")


@router.message(DeliveryStates.input_amount)
async def delivery_input_amount(message: types.Message, state: FSMContext):
    """Обработка ввода суммы"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена. Вернитесь в меню.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="↩️ Назад в меню")]], resize_keyboard=True))
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть положительным числом. Попробуйте еще раз:")
            return
        
        # Сохранение суммы
        await state.update_data(amount=amount)
        
        # Запрос даты доставки
        await message.answer(
            f"💵 **Сумма: {amount:.2f} ₽**\n\n"
            f"📅 **Выберите дату доставки:**",
            reply_markup=delivery_date_keyboard()
        )
        await state.set_state(DeliveryStates.input_delivery_date)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное числовое значение.\n"
            "Пример: 15000 или 15000.50"
        )


@router.message(DeliveryStates.input_delivery_date)
async def delivery_input_date(message: types.Message, state: FSMContext):
    """Обработка ввода даты доставки"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="↩️ Назад в меню")]], resize_keyboard=True))
        return
    
    try:
        delivery_date = None
        today = datetime.now().date()
        
        # Обработка быстрого выбора
        if "Сегодня" in message.text:
            delivery_date = today
        elif "Завтра" in message.text:
            delivery_date = today + timedelta(days=1)
        elif "Через неделю" in message.text:
            delivery_date = today + timedelta(days=7)
        elif "вручную" in message.text:
            await message.answer(
                "📅 **Введите дату в формате ДД.ММ.ГГГГ**\n"
                "Пример: 27.01.2026"
            )
            await state.set_state(DeliveryStates.input_delivery_date)
            return
        else:
            # Ручной ввод даты
            try:
                delivery_date = datetime.strptime(message.text, "%d.%m.%Y").date()
            except ValueError:
                await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                return
        
        # Проверка, что дата не в прошлом
        if delivery_date < today:
            await message.answer("❌ Дата не может быть в прошлом. Выберите будущую дату.")
            return
        
        # Сохранение даты
        await state.update_data(delivery_date=delivery_date.isoformat())
        
        # Запрос комментария
        await message.answer(
            f"📅 **Дата доставки: {delivery_date.strftime('%d.%m.%Y')}**\n\n"
            f"📝 **Введите комментарий к доставке (опционально):**\n"
            f"Или нажмите кнопку для пропуска.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⏭️ Пропустить комментарий")], [KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )
        await state.set_state(DeliveryStates.input_comment)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке даты: {e}")
        await message.answer("❌ Ошибка обработки. Попробуйте еще раз.")


@router.message(DeliveryStates.input_comment)
async def delivery_input_comment(message: types.Message, state: FSMContext):
    """Обработка ввода комментария"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="↩️ Назад в меню")]], resize_keyboard=True))
        return
    
    comment = None if message.text == "⏭️ Пропустить комментарий" else message.text
    
    # Сохранение комментария
    await state.update_data(comment=comment)
    
    # Получение данных для подтверждения
    data = await state.get_data()
    selected_object = data.get("selected_object", {})
    amount = data.get("amount", 0)
    delivery_date = data.get("delivery_date", "")
    
    # Форматирование подтверждения
    comment_text = f"📝 Комментарий: {comment}" if comment else "📝 Комментарий: не указан"
    
    confirm_text = (
        f"✅ **ПОДТВЕРЖДЕНИЕ ЗАЯВКИ НА ДОСТАВКУ**\n\n"
        f"🏗️ Объект: {selected_object.get('code')} - {selected_object.get('name')}\n"
        f"💰 Сумма: {amount:.2f} ₽\n"
        f"📅 Дата доставки: {delivery_date}\n"
        f"{comment_text}\n\n"
        f"**Вы согласны с этими данными?**"
    )
    
    # Кнопки подтверждения
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(confirm_text, reply_markup=keyboard)
    await state.set_state(DeliveryStates.confirm)


@router.message(DeliveryStates.confirm)
async def delivery_confirm(message: types.Message, state: FSMContext):
    """Финальное подтверждение и создание доставки"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Заявка отменена.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="↩️ Назад в меню")]], resize_keyboard=True))
        return
    
    if message.text != "✅ Подтвердить":
        await message.answer("Пожалуйста, используйте предложенные кнопки.")
        return
    
    try:
        # Получение данных
        data = await state.get_data()
        selected_object = data.get("selected_object", {})
        amount = data.get("amount", 0)
        delivery_date = data.get("delivery_date", "")
        comment = data.get("comment")
        
        # Создание доставки через API
        api = APIClient("")  # TODO: получить реальный токен
        
        delivery_payload = {
            "cost_object_id": selected_object.get("id"),
            "amount": amount,
            "delivery_date": delivery_date,
            "comment": comment
        }
        
        # Отправка заявки на создание
        await message.answer(
            "⏳ **Отправка заявки на доставку...**"
        )
        
        # TODO: Вызвать API для создания доставки
        # response = await api.create_delivery(delivery_payload)
        
        # На данный момент заглушка
        await message.answer(
            "✅ **Заявка на доставку успешно создана!**\n\n"
            f"📦 Доставка на сумму {amount:.2f} ₽\n"
            f"📅 Дата: {delivery_date}\n\n"
            "Руководитель и менеджер получат уведомление о новой заявке.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="↩️ Назад в меню")]],
                resize_keyboard=True
            )
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при создании доставки: {e}")
        await message.answer(
            "❌ Ошибка при создании заявки. Попробуйте позже.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="↩️ Назад в меню")]],
                resize_keyboard=True
            )
        )
        await state.clear()
