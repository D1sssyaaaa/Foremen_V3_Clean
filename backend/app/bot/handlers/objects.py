"""Обработчик запросов доступа к объектам"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import get_cancel_keyboard, get_main_menu_keyboard
from app.bot.utils import APIClient

router = Router()


class ObjectAccessStates(StatesGroup):
    """Состояния для запроса доступа к объекту"""
    waiting_for_object = State()
    waiting_for_reason = State()


@router.message(Command("request-access"))
async def cmd_request_access(message: Message, state: FSMContext):
    """Команда /request-access - начало процесса запроса доступа"""
    # Проверяем что пользователь авторизован
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await message.answer(
            "❌ Вы не авторизованы.\n\n"
            "Используйте /start для входа в систему.",
            parse_mode="HTML"
        )
        return
    
    # Получаем список доступных объектов
    try:
        api = APIClient(token=token)
        objects = await api.get_objects(token=token)
        await api.close()
        
        # Логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[BOT] Получены объекты: {len(objects)} шт. Токен: {token[:20]}...")
        
        if not objects:
            await message.answer(
                "ℹ️ <b>В системе нет доступных объектов.</b>\n\n"
                "Обратитесь к руководителю для добавления объектов.",
                parse_mode="HTML"
            )
            return
        
        # Формируем текст
        text = "🏗️ <b>Выберите объект для запроса доступа:</b>"
        
        # Создаем inline клавиатуру
        builder_buttons = []
        for obj in objects:
            obj_code = obj.get('code', 'N/A')
            obj_name = obj.get('name', 'Без названия')[:25]
            obj_id = obj.get('id')
            text_btn = f"{obj_code} - {obj_name}"
            builder_buttons.append([
                InlineKeyboardButton(text=text_btn, callback_data=f"req_obj:{obj_id}")
            ])
        
        # Добавляем кнопку отмены
        builder_buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_access")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=builder_buttons)
        
        # Сохраняем список объектов в состояние
        await state.update_data(available_objects=objects)
        await state.set_state(ObjectAccessStates.waiting_for_object)
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[BOT] Ошибка при загрузке объектов: {str(e)}", exc_info=True)
        
        await message.answer(
            f"❌ <b>Ошибка при загрузке объектов:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("req_obj:"), ObjectAccessStates.waiting_for_object)
async def process_object_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора объекта через callback"""
    try:
        # Получаем ID объекта
        object_id = int(callback.data.split(":")[1])
        
        data = await state.get_data()
        available_objects = data.get("available_objects", [])
        
        # Находим выбранный объект
        selected_object = next((obj for obj in available_objects if obj["id"] == object_id), None)
        
        if not selected_object:
            await callback.answer("❌ Объект не найден")
            return
        
        # Сохраняем выбранный объект
        await state.update_data(selected_object=selected_object)
        
        # Переходим к запросу причины
        await state.set_state(ObjectAccessStates.waiting_for_reason)
        
        await callback.message.edit_text(
            f"✅ Выбран объект: <b>{selected_object['name']}</b>\n\n"
            "📝 Укажите причину запроса доступа (опционально):\n"
            "(Или отправьте /skip для пропуска)",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_reason"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_access")
            ]])
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.message(ObjectAccessStates.waiting_for_reason)
async def process_reason(message: Message, state: FSMContext):
    """Обработка причины запроса"""
    try:
        data = await state.get_data()
        token = data.get("token")
        selected_object = data.get("selected_object")
        
        if not token or not selected_object:
            await message.answer("❌ Ошибка сессии. Начните заново с /request-access")
            await state.clear()
            return
        
        reason = message.text.strip() if message.text else None
        
        # Отправляем запрос на доступ через API
        api = APIClient(token=token)
        result = await api.request_object_access(
            object_id=selected_object["id"],
            reason=reason,
            token=token
        )
        await api.close()
        
        if result:
            # Успешно
            await message.answer(
                f"✅ <b>Запрос отправлен!</b>\n\n"
                f"🏗️ Объект: {selected_object['name']}\n"
                f"📌 Код: {selected_object['code']}\n"
                f"📊 Статус: <b>На рассмотрении</b>\n\n"
                "⏳ Дождитесь одобрения менеджером\n"
                "Проверить статус: /my-requests",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при отправке запроса. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu_keyboard())
        await state.clear()


@router.callback_query(F.data == "skip_reason", ObjectAccessStates.waiting_for_reason)
async def skip_reason(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода причины"""
    await callback.answer()
    
    try:
        data = await state.get_data()
        token = data.get("token")
        selected_object = data.get("selected_object")
        
        if not token or not selected_object:
            await callback.message.edit_text("❌ Ошибка сессии. Начните заново с /request-access")
            await state.clear()
            return
        
        # Отправляем запрос БЕЗ причины
        api = APIClient()
        result = await api.request_object_access(
            object_id=selected_object["id"],
            reason=None,
            token=token
        )
        await api.close()
        
        if result:
            await callback.message.edit_text(
                f"✅ <b>Запрос отправлен!</b>\n\n"
                f"🏗️ Объект: {selected_object['name']}\n"
                f"📌 Код: {selected_object['code']}\n"
                f"📊 Статус: <b>На рассмотрении</b>\n\n"
                "⏳ Дождитесь одобрения менеджером\n"
                "Проверить статус: /my-requests",
                parse_mode="HTML",
                reply_markup=None
            )
            
            await callback.message.answer(
                "📱 Главное меню:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при отправке запроса. Попробуйте позже."
            )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data == "cancel_access")
async def cancel_access_request(callback: CallbackQuery, state: FSMContext):
    """Отмена запроса доступа"""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Запрос доступа отменен.",
        reply_markup=None
    )
    
    await callback.message.answer(
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("my-requests"))
async def cmd_my_requests(message: Message, state: FSMContext):
    """Команда /my-requests - просмотр своих запросов"""
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await message.answer(
            "❌ Вы не авторизованы.\n\n"
            "Используйте /start для входа в систему.",
            parse_mode="HTML"
        )
        return
    
    try:
        api = APIClient(token=token)
        requests = await api.get_my_access_requests(token=token)
        await api.close()
        
        if not requests:
            await message.answer(
                "ℹ️ У вас нет запросов на доступ.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        text = "📋 <b>Ваши запросы на доступ:</b>\n\n"
        
        for req in requests:
            status_emoji = {
                "PENDING": "⏳",
                "APPROVED": "✅",
                "REJECTED": "❌"
            }.get(req.get("status"), "❓")
            
            status_text = {
                "PENDING": "На рассмотрении",
                "APPROVED": "Одобрено",
                "REJECTED": "Отклонено"
            }.get(req.get("status"), req.get("status"))
            
            text += f"{status_emoji} <b>{req.get('object_name')}</b>\n"
            text += f"   Код: {req.get('object_code')}\n"
            text += f"   Статус: {status_text}\n"
            
            if req.get("rejection_reason"):
                text += f"   Причина отклонения: {req.get('rejection_reason')}\n"
            
            text += "\n"
        
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
