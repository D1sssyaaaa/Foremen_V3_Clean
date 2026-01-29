"""Хэндлеры для создания заявок на технику"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from app.bot.states import EquipmentOrderStates
from app.bot.keyboards import (
    get_equipment_type_keyboard,
    get_yes_no_keyboard,
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_objects_keyboard
)
from app.bot.utils import APIClient

router = Router()


@router.message(F.text == "🚜 Заявка на технику")
async def start_equipment_order(message: Message, state: FSMContext):
    """Начало создания заявки на технику"""
    # Получаем токен из состояния
    data = await state.get_data()
    token = data.get('token')
    
    if not token:
        await message.answer(
            "❌ Ошибка авторизации. Отправьте /start для повторной авторизации.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Получаем список объектов из API
    api = APIClient(token)
    try:
        objects = await api.get_objects()
        await api.close()
        
        if not objects:
            await message.answer(
                "❌ Нет доступных объектов учета.\n"
                "Обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(
            "🚜 <b>Создание заявки на технику</b>\n\n"
            "Выберите объект учета:",
            parse_mode="HTML",
            reply_markup=get_objects_keyboard(objects)
        )
        await state.set_state(EquipmentOrderStates.select_object)
    except Exception as e:
        await api.close()
        await message.answer(
            f"❌ Ошибка при загрузке объектов: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(F.data.startswith("object:"), EquipmentOrderStates.select_object)
async def process_select_object(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора объекта через кнопку"""
    object_id = int(callback.data.split(":")[1])
    await state.update_data(cost_object_id=object_id)
    await callback.answer()
    
    await callback.message.edit_text(
        "🔧 <b>Выберите тип техники:</b>",
        parse_mode="HTML",
        reply_markup=get_equipment_type_keyboard()
    )
    await state.set_state(EquipmentOrderStates.select_equipment_type)


@router.callback_query(F.data.startswith("eqtype:"))
async def process_equipment_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа техники"""
    equipment_type = callback.data.split(":")[1]
    await state.update_data(equipment_type=equipment_type)
    await callback.answer()
    
    from app.bot.keyboards import get_date_selection_keyboard
    
    equipment_labels = {
        "excavator": "🏗️ Экскаватор",
        "crane": "🏗️ Кран",
        "bulldozer": "🚜 Бульдозер",
        "loader": "🚚 Погрузчик",
        "mixer": "🥤 Бетономешалка",
        "other": "🔧 Другое"
    }
    
    await callback.message.edit_text(
        f"Выбрана техника: {equipment_labels.get(equipment_type, equipment_type)}\n\n"
        "📅 <b>Выберите дату начала работ:</b>",
        parse_mode="HTML",
        reply_markup=get_date_selection_keyboard()
    )
    await state.set_state(EquipmentOrderStates.select_start_date)


@router.callback_query(F.data.startswith("date:"), EquipmentOrderStates.select_start_date)
async def process_start_date_button(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты начала через кнопку"""
    date_value = callback.data.split(":")[1]
    
    if date_value == "custom":
        await callback.message.edit_text(
            "📅 Введите дату начала работ в формате <code>ДД.ММ.ГГГГ</code>:\n"
            "Например: <code>26.01.2026</code>",
            parse_mode="HTML"
        )
        await state.set_state(EquipmentOrderStates.input_start_date)
        await callback.answer()
        return
    
    # Сохраняем выбранную дату
    await state.update_data(start_date=date_value)
    await callback.answer()
    
    await callback.message.edit_text(
        f"📅 Дата начала: {date_value}\n\n"
        "⏰ Введите количество дней аренды (число):",
        parse_mode="HTML"
    )
    await state.set_state(EquipmentOrderStates.input_duration)


@router.message(EquipmentOrderStates.input_start_date)
async def process_start_date(message: Message, state: FSMContext):
    """Обработка даты начала"""
    try:
        date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        
        if date_obj < datetime.now().date():
            await message.answer("❌ Дата должна быть в будущем или сегодня")
            return
        
        await state.update_data(start_date=date_obj.isoformat())
        
        await message.answer(
            "⏰ Введите количество дней аренды (число):",
            parse_mode="HTML"
        )
        await state.set_state(EquipmentOrderStates.input_duration)
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты.\n"
            "Используйте формат ДД.ММ.ГГГГ, например: 26.01.2026"
        )


@router.message(EquipmentOrderStates.input_duration)
async def process_duration(message: Message, state: FSMContext):
    """Обработка длительности аренды"""
    try:
        days = int(message.text.strip())
        if days <= 0:
            await message.answer("❌ Количество дней должно быть больше нуля")
            return
        
        await state.update_data(duration_days=days)
        
        await message.answer(
            "📝 Введите описание работ (или пропустите, отправив '-'):",
            parse_mode="HTML"
        )
        await state.set_state(EquipmentOrderStates.input_description)
    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.message(EquipmentOrderStates.input_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания работ"""
    description = message.text.strip()
    if description == "-":
        description = None
    
    await state.update_data(description=description)
    
    # Показываем предпросмотр
    data = await state.get_data()
    
    equipment_labels = {
        "excavator": "🏗️ Экскаватор",
        "crane": "🏗️ Кран",
        "bulldozer": "🚜 Бульдозер",
        "loader": "🚚 Погрузчик",
        "mixer": "🥤 Бетономешалка",
        "other": "🔧 Другое"
    }
    
    preview = (
        "📋 <b>Предпросмотр заявки на технику:</b>\n\n"
        f"🏗️ Объект: #{data['cost_object_id']}\n"
        f"🔧 Техника: {equipment_labels.get(data['equipment_type'], data['equipment_type'])}\n"
        f"📅 Дата начала: {data['start_date']}\n"
        f"⏰ Длительность: {data['duration_days']} дн.\n"
    )
    
    if data.get('description'):
        preview += f"📝 Описание: {data['description']}\n"
    
    preview += "\n✅ Подтвердить создание заявки?"
    
    await message.answer(
        preview,
        parse_mode="HTML",
        reply_markup=get_confirm_keyboard()
    )
    await state.set_state(EquipmentOrderStates.confirm)


@router.callback_query(F.data == "confirm_yes", EquipmentOrderStates.confirm)
async def process_confirm_yes(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заявки"""
    data = await state.get_data()
    token = data.get('token')
    
    if not token:
        await callback.message.edit_text(
            "❌ Ошибка авторизации. Отправьте /start для повторной авторизации."
        )
        await callback.message.answer(
            "📱 Главное меню:", 
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        await callback.answer()
        return
    
    api = APIClient(token)
    
    try:
        # Вычисляем end_date из start_date + duration_days
        from datetime import datetime, timedelta
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=data['duration_days'])
        
        # Формируем запрос
        request_data = {
            "cost_object_id": data['cost_object_id'],
            "equipment_type": data['equipment_type'],
            "start_date": data['start_date'],
            "end_date": end_date.strftime("%Y-%m-%d"),
            "supplier": None,  # Будет заполнено позже
            "comment": data.get('description')
        }
        
        # Отправляем заявку
        result = await api.create_equipment_request(request_data)
        await api.close()
        
        await callback.message.edit_text(
            f"✅ <b>Заявка на технику создана!</b>\n\n"
            f"📝 Номер заявки: #{result.get('id', 'N/A')}\n"
            f"📊 Статус: {result.get('status', 'N/A')}\n\n"
            "Ожидайте утверждения от менеджера по технике.\n"
            "Вы получите уведомление при изменении статуса.",
            parse_mode="HTML"
        )
        await callback.message.answer(
            "📱 Главное меню:", 
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        await api.close()
        await callback.message.edit_text(
            f"❌ <b>Ошибка при создании заявки:</b>\n\n"
            f"{str(e)}",
            parse_mode="HTML"
        )
        await callback.message.answer(
            "📱 Главное меню:", 
            reply_markup=get_main_menu_keyboard()
        )
    
    # Сохраняем токен перед очисткой
    token = data.get('token')
    await state.clear()
    if token:
        await state.update_data(token=token)
    await callback.answer()


@router.callback_query(F.data == "confirm_no", EquipmentOrderStates.confirm)
async def process_confirm_no(callback: CallbackQuery, state: FSMContext):
    """Отмена создания заявки"""
    await callback.message.edit_text(
        "❌ Создание заявки отменено."
    )
    await callback.message.answer(
        "📱 Главное меню:", 
        reply_markup=get_main_menu_keyboard()
    )
    
    # Сохраняем токен
    data = await state.get_data()
    token = data.get('token')
    await state.clear()
    if token:
        await state.update_data(token=token)
    await callback.answer()
