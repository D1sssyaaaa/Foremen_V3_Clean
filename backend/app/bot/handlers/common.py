"""Базовые команды бота"""
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import (
    get_main_menu_keyboard, 
    get_register_keyboard,
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_manager_dashboard_keyboard
)
from app.bot.config import config
from app.bot.utils import APIClient
from app.bot.states import RegistrationStates

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    await state.clear()
    
    # Авторизация через Telegram ID
    api = APIClient()
    token = await api.login_telegram(message.from_user.id)
    await api.close()
    
    if token:
        # Сохраняем токен в состояние пользователя
        await state.update_data(token=token)
        
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
            "🏗️ <b>Система учета затрат строительной компании</b>\n\n"
            "Я помогу вам:\n"
            "• 📦 Создавать заявки на материалы (включая инертные)\n"
            "• 🚜 Заказывать технику и инструмент\n"
            "• 📊 Подавать табели рабочего времени\n"
            "• 📈 Отслеживать статусы заявок\n\n"
            "Выберите действие из меню ⬇️"
        )
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Проверяем, может ли пользователь подать заявку на регистрацию
        api2 = APIClient()
        registration_request = await api2.check_registration_request_status(message.from_user.id)
        await api2.close()
        
        if registration_request:
            # Заявка уже подана
            status = registration_request.get("status", "").upper()
            status_text = {
                "PENDING": "⏳ На рассмотрении",
                "APPROVED": "✅ Одобрена",
                "REJECTED": "❌ Отклонена"
            }.get(status, status)
            
            welcome_text = (
                f"👋 Здравствуйте, {message.from_user.full_name}!\n\n"
                "🏗️ <b>Система учета затрат строительной компании</b>\n\n"
                f"📊 <b>Статус вашей заявки на регистрацию:</b> {status_text}\n\n"
            )
            
            if status == "REJECTED":
                reason = registration_request.get("rejection_reason", "не указана")
                welcome_text += f"❌ <b>Причина отклонения:</b>\n{reason}\n\n"
                welcome_text += "Вы можете подать новую заявку командой /register"
                keyboard = get_register_keyboard()
            elif status == "APPROVED":
                welcome_text += "✨ Приступите к привязке аккаунта командой /link"
                keyboard = None
            else:
                welcome_text += "Дождитесь решения руководителя..."
                keyboard = None
            
            await message.answer(
                welcome_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            # Нет заявки - предлагаем создать
            welcome_text = (
                f"👋 Здравствуйте, {message.from_user.full_name}!\n\n"
                "🏗️ <b>Система учета затрат строительной компании</b>\n\n"
                "❌ Ваш Telegram аккаунт не зарегистрирован в системе.\n\n"
                "Вы можете <b>подать заявку на регистрацию</b> в качестве бригадира.\n"
                "После проверки руководителем вам откроется доступ.\n\n"
                f"📱 Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
                f"👤 Имя: <code>{message.from_user.full_name}</code>"
            )
            await message.answer(
                welcome_text,
                parse_mode="HTML",
                reply_markup=get_register_keyboard()
            )


# ===== Регистрация теперь обрабатывается в registration.py =====


@router.message(Command("manager"))
async def cmd_manager(message: Message, state: FSMContext):
    """Команда /manager для открытия панели руководителя"""
    # В идеале нужно проверять роль пользователя, но пока просто отправляем ссылку
    # URL для Mini App
    url = f"{config.web_app_url.rstrip('/')}/manager-dashboard"
    # Для WebApp URL должен быть абсолютным и HTTPS. 
    # Если мы локально, это может не сработать без туннеля, но ссылка будет правильной.
    
    await message.answer(
        "📊 <b>Панель руководителя</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть сводку по объектам:",
        parse_mode="HTML",
        reply_markup=get_manager_dashboard_keyboard(url)
    )


# ===== Мои заявки =====

@router.message(F.text == "📈 Мои заявки")
async def my_requests(message: Message, state: FSMContext):
    """Просмотр своих заявок"""
    data = await state.get_data()
    token = data.get('token')
    
    if not token:
        await message.answer(
            "❌ Ошибка авторизации. Отправьте /start для повторной авторизации.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    api = APIClient(token)
    try:
        # Получаем заявки на материалы и технику
        material_requests = await api.get_my_material_requests()
        equipment_requests = await api.get_my_equipment_requests()
        await api.close()
        
        if not material_requests and not equipment_requests:
            await message.answer(
                "📋 <b>Ваши заявки</b>\n\n"
                "У вас пока нет заявок.\n\n"
                "Создайте первую заявку через меню!",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        text = "📋 <b>Ваши заявки:</b>\n\n"
        
        material_status_emoji = {
            "НОВАЯ": "🆕",
            "НА СОГЛАСОВАНИИ": "⏳",
            "В ОБРАБОТКЕ": "🔄",
            "ЗАКАЗАНО": "📦",
            "ЧАСТИЧНО ПОСТАВЛЕНО": "📬",
            "ОТГРУЖЕНО": "🚚",
            "ВЫПОЛНЕНА": "✅"
        }
        
        equipment_status_emoji = {
            "НОВАЯ": "🆕",
            "УТВЕРЖДЕНА": "✅",
            "В РАБОТЕ": "🔄",
            "ЗАВЕРШЕНА": "✔️",
            "ОТМЕНА ЗАПРОШЕНА": "⏳",
            "ОТМЕНЕНА": "❌"
        }
        
        # Перевод типов техники
        equipment_type_translation = {
            "loader": "Погрузчик",
            "excavator": "Экскаватор",
            "crane": "Кран",
            "truck": "Грузовик",
            "bulldozer": "Бульдозер",
            "concrete_mixer": "Бетономешалка",
            "compactor": "Каток",
            "forklift": "Вилочный погрузчик"
        }
        
        # Кнопки для детального просмотра
        keyboard = []
        
        # Заявки на материалы
        if material_requests:
            text += "📦 <b>Материалы:</b>\n"
            for req in material_requests[:5]:  # Последние 5
                emoji = material_status_emoji.get(req.get('status', ''), '📝')
                date_str = req.get('created_at', '')[:10] if req.get('created_at') else ''
                text += f"{emoji} <b>#{req.get('id')}</b> — {req.get('status', 'N/A')}\n"
                text += f"   📅 {date_str}\n"
                
                # Кнопка для просмотра деталей
                keyboard.append([InlineKeyboardButton(
                    text=f"📦 Материалы #{req.get('id')}",
                    callback_data=f"view_material_{req.get('id')}"
                )])
            text += "\n"
        
        # Заявки на технику
        if equipment_requests:
            text += "🚜 <b>Техника:</b>\n"
            for req in equipment_requests[:5]:  # Последние 5
                emoji = equipment_status_emoji.get(req.get('status', ''), '📝')
                date_str = req.get('created_at', '')[:10] if req.get('created_at') else ''
                equipment_type = req.get('equipment_type', 'N/A')
                # Переводим тип техники на русский
                equipment_type_ru = equipment_type_translation.get(equipment_type, equipment_type)
                text += f"{emoji} <b>#{req.get('id')}</b> — {equipment_type_ru}\n"
                text += f"   📊 {req.get('status', 'N/A')} | 📅 {date_str}\n"
                
                # Кнопка для просмотра деталей
                keyboard.append([InlineKeyboardButton(
                    text=f"🚜 Техника #{req.get('id')}",
                    callback_data=f"view_equipment_{req.get('id')}"
                )])
            text += "\n"
        
        text += "Нажмите на кнопку для просмотра деталей заявки."
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
        
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await api.close()
        await message.answer(
            f"❌ Ошибка при загрузке заявок: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data.startswith("view_material_"))
async def view_material_request_details(callback: CallbackQuery, state: FSMContext):
    """Просмотр деталей заявки на материалы"""
    request_id = callback.data.split("_")[2]
    
    data = await state.get_data()
    token = data.get('token')
    
    if not token:
        await callback.answer("❌ Ошибка авторизации", show_alert=True)
        return
    
    api = APIClient(token)
    try:
        # Получаем детальную информацию о заявке (включая items)
        request = await api.get_material_request_details(int(request_id))
        await api.close()
        
        if not request:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Перевод срочности
        urgency_translation = {
            "critical": "Критическая",
            "urgent": "Срочная",
            "high": "Высокая",
            "normal": "Обычная",
            "low": "Низкая"
        }
        
        # Перевод статуса
        status_translation = {
            "NEW": "Новая",
            "PENDING_APPROVAL": "На согласовании",
            "IN_PROGRESS": "В обработке",
            "ORDERED": "Заказано",
            "PARTIALLY_DELIVERED": "Частично поставлено",
            "DELIVERED": "Отгружено",
            "COMPLETED": "Выполнена",
            "REJECTED": "Отклонена",
            "CANCELLED": "Отменена"
        }
        
        # Формируем детальное описание
        text = f"📦 <b>Заявка на материалы #{request.get('id')}</b>\n\n"
        text += f"🏗 <b>Объект:</b> {request.get('cost_object_name', 'N/A')}\n"
        
        # Переводим статус на русский
        status = request.get('status', 'N/A')
        status_ru = status_translation.get(status, status)
        text += f"📊 <b>Статус:</b> {status_ru}\n"
        
        # Переводим срочность на русский
        urgency = request.get('urgency', 'N/A')
        urgency_ru = urgency_translation.get(urgency, urgency)
        text += f"🔥 <b>Срочность:</b> {urgency_ru}\n"
        
        # Дата создания
        created_at = request.get('created_at', '')
        if created_at:
            text += f"📅 <b>Создано:</b> {created_at[:10]}\n"
        
        if request.get('expected_delivery_date'):
            text += f"🚚 <b>Желаемая дата:</b> {request.get('expected_delivery_date')}\n"
        
        if request.get('delivery_time'):
            text += f"⏰ <b>Время доставки:</b> {request.get('delivery_time')}\n"
        
        if request.get('comment'):
            text += f"💬 <b>Комментарий:</b> {request.get('comment')}\n"
        
        # Позиции материалов
        items = request.get('items', [])
        if items:
            text += f"\n📦 <b>Материалы ({len(items)}):</b>\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item.get('material_name')} — {item.get('quantity')} {item.get('unit')}\n"
                if item.get('description'):
                    text += f"   <i>{item.get('description')}</i>\n"
        else:
            text += "\n⚠️ <i>Материалы не указаны</i>\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_requests")
            ]])
        )
        await callback.answer()
        
    except Exception as e:
        await api.close()
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("view_equipment_"))
async def view_equipment_request_details(callback: CallbackQuery, state: FSMContext):
    """Просмотр деталей заявки на технику"""
    request_id = callback.data.split("_")[2]
    
    data = await state.get_data()
    token = data.get('token')
    
    if not token:
        await callback.answer("❌ Ошибка авторизации", show_alert=True)
        return
    
    api = APIClient(token)
    try:
        # Получаем все заявки и находим нужную
        requests = await api.get_my_equipment_requests()
        await api.close()
        
        request = next((r for r in requests if str(r.get('id')) == request_id), None)
        
        if not request:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Перевод типов техники
        equipment_type_translation = {
            "loader": "Погрузчик",
            "excavator": "Экскаватор",
            "crane": "Кран",
            "truck": "Грузовик",
            "bulldozer": "Бульдозер",
            "concrete_mixer": "Бетономешалка",
            "compactor": "Каток",
            "forklift": "Вилочный погрузчик"
        }
        
        # Функция для форматирования даты
        def format_date(date_str):
            if not date_str:
                return 'N/A'
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
                return f"{date_obj.day} {months[date_obj.month-1]}"
            except:
                return date_str
        
        # Формируем детальное описание
        text = f"🚜 <b>Заявка на технику #{request.get('id')}</b>\n\n"
        text += f"🏗 <b>Объект:</b> {request.get('cost_object_name', 'N/A')}\n"
        text += f"📊 <b>Статус:</b> {request.get('status', 'N/A')}\n"
        
        # Переводим тип техники на русский
        equipment_type = request.get('equipment_type', 'N/A')
        equipment_type_ru = equipment_type_translation.get(equipment_type, equipment_type)
        text += f"🚜 <b>Тип:</b> {equipment_type_ru}\n\n"
        
        if request.get('start_date') and request.get('end_date'):
            start = format_date(request.get('start_date'))
            end = format_date(request.get('end_date'))
            text += f"📅 <b>Период:</b> {start} — {end}\n"
        elif request.get('start_date'):
            text += f"📅 <b>Начало:</b> {format_date(request.get('start_date'))}\n"
        
        created = format_date(request.get('created_at', '')[:10])
        text += f"📝 <b>Создано:</b> {created}\n"
        
        if request.get('supplier'):
            text += f"🏢 <b>Поставщик:</b> {request.get('supplier')}\n"
        
        if request.get('comment'):
            text += f"\n💬 <b>Комментарий:</b> {request.get('comment')}\n"
        
        if request.get('cancel_reason'):
            text += f"\n❌ <b>Причина отмены:</b> {request.get('cancel_reason')}\n"
        
        # Формируем кнопки
        keyboard_buttons = []
        
        # Кнопка отмены - только для статусов НОВАЯ и УТВЕРЖДЕНА
        status = request.get('status', '')
        if status in ['НОВАЯ', 'УТВЕРЖДЕНА']:
            keyboard_buttons.append([InlineKeyboardButton(
                text="❌ Отменить заявку", 
                callback_data=f"cancel_equipment_{request.get('id')}"
            )])
        
        # Кнопка "Назад"
        keyboard_buttons.append([InlineKeyboardButton(
            text="◀️ Назад к списку", 
            callback_data="back_to_requests"
        )])
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        )
        await callback.answer()
        
    except Exception as e:
        await api.close()
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("cancel_equipment_"))
async def start_cancel_equipment(callback: CallbackQuery, state: FSMContext):
    """Начало процесса отмены заявки на технику"""
    order_id = callback.data.split("_")[2]
    
    await state.update_data(cancel_order_id=order_id)
    
    await callback.message.edit_text(
        f"❌ <b>Отмена заявки #{order_id}</b>\n\n"
        "Пожалуйста, укажите причину отмены:\n\n"
        "<i>Например: «Техника больше не нужна» или «Изменились сроки»</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Отмена", callback_data=f"view_equipment_{order_id}")
        ]])
    )
    
    from app.bot.states import EquipmentOrderStates
    await state.set_state(EquipmentOrderStates.cancel_reason)
    await callback.answer()


from app.bot.states import EquipmentOrderStates as EqStates

@router.message(EqStates.cancel_reason)
async def process_cancel_reason(message: Message, state: FSMContext):
    """Обработка причины отмены заявки на технику"""
    data = await state.get_data()
    token = data.get('token')
    order_id = data.get('cancel_order_id')
    reason = message.text.strip()
    
    if not token or not order_id:
        await message.answer(
            "❌ Ошибка. Попробуйте снова через «📈 Мои заявки».",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(None)
        return
    
    if len(reason) < 5:
        await message.answer(
            "❌ Причина слишком короткая. Пожалуйста, опишите подробнее."
        )
        return
    
    api = APIClient(token)
    try:
        result = await api.request_cancel_equipment(int(order_id), reason)
        await api.close()
        
        await message.answer(
            f"✅ <b>Запрос на отмену заявки #{order_id} отправлен!</b>\n\n"
            f"📝 Причина: {reason}\n\n"
            "Менеджер рассмотрит ваш запрос и примет решение.\n"
            "Вы получите уведомление о результате.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        await api.close()
        error_msg = str(e)
        if "422" in error_msg or "400" in error_msg:
            await message.answer(
                f"❌ Невозможно отменить заявку.\n\n"
                f"Возможно, её статус уже изменился.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                f"❌ Ошибка при отмене заявки: {error_msg}",
                reply_markup=get_main_menu_keyboard()
            )
    
    # Сбрасываем состояние, но сохраняем токен
    await state.set_state(None)
    await state.update_data(cancel_order_id=None)


@router.callback_query(F.data == "back_to_requests")
async def back_to_requests_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку заявок"""
    # Вызываем функцию отображения списка заново
    await callback.message.delete()
    await my_requests(callback.message, state)


# ===== Помощь =====

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "📖 <b>Помощь по командам</b>\n\n"
        
        "<b>📦 Заявка на материалы:</b>\n"
        "Создание заявки на материалы для объекта.\n"
        "Для <b>инертных материалов</b> (песок, щебень, раствор) "
        "обязательно указывается желаемое время доставки.\n\n"
        
        "Формат ввода материалов:\n"
        "<code>Название количество ед.изм</code>\n"
        "Пример: <code>Песок 10 т</code>\n\n"
        
        "<b>🚜 Заявка на технику:</b>\n"
        "Заказ техники или инструмента в аренду.\n\n"
        
        "<b>📊 Табель РТБ:</b>\n"
        "Подача табеля рабочего времени бригады.\n"
        "Можно загрузить Excel файл или ввести вручную.\n\n"
        
        "<b>📈 Мои заявки:</b>\n"
        "Просмотр всех ваших заявок и их статусов.\n\n"
        
        "❓ По вопросам обращайтесь к вашему менеджеру."
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    data = await state.get_data()
    token = data.get('token')
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await message.answer(
        "❌ Действие отменено.\n\nВыберите новое действие из меню.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("link"))
async def cmd_link(message: Message, state: FSMContext):
    """
    Команда /link для привязки аккаунта
    Используется: /link <код>
    Пример: /link 123456
    """
    # Парсим команду и код
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer(
            "ℹ️ <b>Привязка Telegram аккаунта</b>\n\n"
            "Команда: <code>/link КОД</code>\n\n"
            "Как это работает:\n"
            "1. Откройте веб-приложение\n"
            "2. Перейдите в свой профиль\n"
            "3. Нажмите 'Генерировать код привязки'\n"
            "4. Скопируйте полученный код\n"
            "5. Отправьте: <code>/link КОД</code>\n\n"
            "Пример: <code>/link 123456</code>",
            parse_mode="HTML"
        )
        return
    
    code = parts[1]
    
    # Валидируем код
    if not code.isdigit() or len(code) != 6:
        await message.answer(
            "❌ Неверный формат кода. Код должен состоять из 6 цифр.\n\n"
            "Пример: <code>/link 123456</code>",
            parse_mode="HTML"
        )
        return
    
    # Отправляем запрос на привязку
    api = APIClient()
    try:
        result = await api.link_telegram_account(
            code=code,
            telegram_chat_id=str(message.from_user.id),
            telegram_username=message.from_user.username
        )
        
        if result and result.get("success"):
            success_text = (
                f"✅ <b>Успешно!</b>\n\n"
                f"{result.get('message', 'Аккаунт привязан')}\n\n"
                "📱 Теперь вы можете использовать все функции системы!"
            )
            await message.answer(success_text, parse_mode="HTML")
            
            # Очищаем состояние и показываем главное меню
            await state.clear()
            welcome_text = (
                f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
                "🏗️ <b>Система учета затрат строительной компании</b>\n\n"
                "Выберите действие из меню ⬇️"
            )
            await message.answer(
                welcome_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            error_msg = result.get("detail", "Неизвестная ошибка") if result else "Ошибка сервера"
            await message.answer(
                f"❌ <b>Ошибка</b>\n\n{error_msg}",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка при привязке аккаунта</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    finally:
        await api.close()


# ===== Запрос доступа =====

@router.message(F.text == "🏗️ Запросить доступ")
async def request_access_menu(message: Message, state: FSMContext):
    """Обработка нажатия на кнопку 'Запросить доступ'"""
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await message.answer("❌ Вы не авторизованы. Используйте /start для входа.")
        return
    
    # Перенаправляем на команду /request-access
    from app.bot.handlers.objects import cmd_request_access
    await cmd_request_access(message, state)