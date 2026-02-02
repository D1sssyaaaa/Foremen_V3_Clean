
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re

from app.bot.states import RegistrationStates
from app.bot.keyboards import (
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_role_selection_keyboard,
    get_main_menu_keyboard
)
from app.bot.utils.api_client import APIClient

router = Router()

@router.callback_query(F.data == "register_start")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    """Начало процесса регистрации"""
    await callback.answer()
    
    # Сохраняем telegram данные
    await state.update_data(
        telegram_user_id=str(callback.from_user.id),
        telegram_username=callback.from_user.username
    )
    
    await callback.message.edit_text(
        "📝 <b>Заявка на регистрацию</b>\n\n"
        "Шаг 1 из 4\n\n"
        "👤 Введите ваше <b>ФИО</b>:\n"
        "<i>Например: Иванов Иван Иванович</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.input_full_name)


@router.message(RegistrationStates.input_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода ФИО"""
    full_name = message.text.strip()
    
    if len(full_name) < 5:
        await message.answer(
            "❌ ФИО слишком короткое.\n"
            "Введите полное имя (минимум 5 символов):",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if len(full_name) > 100:
        await message.answer(
            "❌ ФИО слишком длинное.\n"
            "Введите корректное ФИО (максимум 100 символов):",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(full_name=full_name)
    
    await message.answer(
        "📝 <b>Заявка на регистрацию</b>\n\n"
        "Шаг 2 из 4\n\n"
        "📅 Введите вашу <b>дату рождения</b>:\n"
        "<i>Формат: ДД.ММ.ГГГГ</i>\n"
        "<i>Например: 15.03.1985</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.input_birth_date)


@router.message(RegistrationStates.input_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка ввода даты рождения"""
    try:
        birth_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        
        # Проверка возраста (минимум 16 лет)
        today = datetime.now().date()
        age = (today - birth_date).days // 365
        
        if age < 16:
            await message.answer(
                "❌ Минимальный возраст для регистрации — 16 лет.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        if age > 100:
            await message.answer(
                "❌ Проверьте правильность даты рождения.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await state.update_data(birth_date=birth_date.isoformat())
        
        await message.answer(
            "📝 <b>Заявка на регистрацию</b>\n\n"
            "Шаг 3 из 4\n\n"
            "📱 Введите ваш <b>номер телефона</b>:\n"
            "<i>Например: +7 999 123-45-67</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(RegistrationStates.input_phone)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Введите дату в формате <code>ДД.ММ.ГГГГ</code>\n"
            "Например: <code>15.03.1985</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )


@router.message(RegistrationStates.input_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()
    
    # Очистка и валидация телефона
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?[0-9]{10,15}$', phone_clean):
        await message.answer(
            "❌ Некорректный номер телефона.\n"
            "Введите номер в формате: +7 999 123-45-67",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(phone=phone_clean)
    
    # Переход к выбору роли
    await message.answer(
        "📝 <b>Заявка на регистрацию</b>\n\n"
        "Шаг 4 из 4\n\n"
        "👔 Выберите <b>желаемую должность</b>:",
        parse_mode="HTML",
        reply_markup=get_role_selection_keyboard()
    )
    await state.set_state(RegistrationStates.select_role)


@router.callback_query(F.data.startswith("role:"), RegistrationStates.select_role)
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли"""
    role_code = callback.data.split(":")[1]
    
    role_names = {
        "FOREMAN": "Бригадир",
        "EQUIPMENT_MANAGER": "Менеджер по технике",
        "MATERIALS_MANAGER": "Менеджер по снабжению",
        "ACCOUNTANT": "Бухгалтер",
        "MANAGER": "Руководитель"
    }
    role_name = role_names.get(role_code, role_code)
    
    await state.update_data(requested_role=role_code, role_name=role_name)
    
    # Показываем превью
    data = await state.get_data()
    birth_date_str = datetime.fromisoformat(data['birth_date']).strftime('%d.%m.%Y')
    
    preview_text = (
        "📋 <b>Проверьте ваши данные:</b>\n\n"
        f"👤 ФИО: <b>{data.get('full_name')}</b>\n"
        f"📅 Дата рождения: <b>{birth_date_str}</b>\n"
        f"📱 Телефон: <b>{data.get('phone')}</b>\n"
        f"👔 Должность: <b>{role_name}</b>\n"
        f"💬 Telegram: <b>@{data.get('telegram_username') or data.get('telegram_user_id')}</b>\n\n"
        "Отправить заявку на регистрацию?"
    )
    
    await callback.message.edit_text(
        preview_text,
        parse_mode="HTML",
        reply_markup=get_confirm_keyboard()
    )
    await state.set_state(RegistrationStates.confirm)
    await callback.answer()


@router.callback_query(F.data == "confirm_yes", RegistrationStates.confirm)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка заявки на регистрацию"""
    await callback.answer("Отправка заявки...")
    
    data = await state.get_data()
    
    # Формируем данные для API
    request_data = {
        "full_name": data.get('full_name'),
        "birth_date": data.get('birth_date'),
        "phone": data.get('phone'),
        "telegram_chat_id": str(callback.message.chat.id),
        "telegram_username": data.get('telegram_username'),
        "requested_role": data.get('requested_role')
    }
    
    api = APIClient()
    try:
        result = await api.create_registration_request(request_data)
        await api.close()
        
        await callback.message.edit_text(
            "✅ <b>Заявка отправлена!</b>\n\n"
            f"📝 Номер заявки: <code>#{result.get('id')}</code>\n"
            f"👔 Запрошенная роль: <b>{data.get('role_name')}</b>\n\n"
            "Ваша заявка будет рассмотрена руководителем.\n"
            "Вы получите уведомление о решении.\n\n"
            "Для проверки статуса отправьте /start",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await api.close()
        error_msg = str(e)
        
        if "уже существует" in error_msg.lower() or "already" in error_msg.lower():
            await callback.message.edit_text(
                "❌ <b>Заявка уже существует</b>\n\n"
                "Вы уже подавали заявку на регистрацию.\n"
                "Дождитесь её рассмотрения или обратитесь к руководителю.",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Ошибка при отправке заявки</b>\n\n"
                f"{error_msg}\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML"
            )
        await state.clear()


@router.callback_query(F.data == "confirm_no", RegistrationStates.confirm)
async def cancel_registration_confirm(callback: CallbackQuery, state: FSMContext):
    """Отмена на этапе подтверждения"""
    await callback.answer("Заявка отменена")
    await state.clear()
    await callback.message.edit_text(
        "❌ Заявка отменена.\n\n"
        "Выберите действие из меню."
    )
    await callback.message.answer(
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "cancel_registration")
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Отмена регистрации"""
    await callback.answer("Отменено")
    await state.clear()
    await callback.message.edit_text(
        "❌ Регистрация отменена."
    )
    await callback.message.answer(
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
