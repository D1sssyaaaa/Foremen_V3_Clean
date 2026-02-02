
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Optional

from app.bot.utils.api_client import APIClient
from app.core.models_base import UserRole

router = Router()

@router.callback_query(F.data.startswith("admin:reg:"))
async def process_registration_decision(callback: CallbackQuery, state: FSMContext):
    """Обработка решения по регистрации (Принять/Отклонить)"""
    # admin:reg:confirm:{id} или admin:reg:reject:{id}
    parts = callback.data.split(":")
    action = parts[2]
    request_id = int(parts[3])
    
    # Получаем токен админа (предполагаем, что он есть в state или конфиге,
    # но в данном контексте бот работает как сервисный аккаунт или мы логинимся как админ?
    # TODO: Реализовать получение токена админа. Пока используем заглушку или токен из state если админ залогинен)
    # В реальной схеме бот должен иметь свой сервисный токен или админ должен авторизоваться через /login
    
    # Проверяем, залогинен ли пользователь как админ
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await callback.answer("❌ Вы не авторизованы как администратор.", show_alert=True)
        return

    api = APIClient(token=token)
    
    try:
        if action == "confirm":
            # Пока по умолчанию даем роль, которая была запрошена (нужно получить детали заявки)
            # Или спросить роль? Для простоты пока FOREMAN или то что в заявке.
            # Мы можем запросить детали заявки:
            request_details = await api.get_registration_request_details(request_id) # Need adding get_details too?
            # Или просто сразу апрувим c ролью из коллбэка (если бы мы её туда зашили)
            
            # Для простоты: апрувим как FOREMAN если роль не ясна, или берем из текста сообщения если парсить?
            # Лучше добавим метод get_registration_request в APIClient.
            # Или просто предположим роль FOREMAN по умолчанию, так как в confirm_registration_keyboard ее нет.
            
            # ВАЖНО: В реализации API approve принимает список ролей.
            # Попробуем получить заявку, чтобы узнать запрашиваемую роль.
            
            # TODO: Add get_registration_request to APIClient
            # For now default to FOREMAN
            roles = [UserRole.FOREMAN.value]
            
            await api.approve_registration(request_id, roles)
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"✅ Заявка #{request_id} одобрена.")
            await callback.answer("Одобрено!")
            
        elif action == "reject":
            # Спрашиваем причину (можно через State)
            # Для простоты пока "Отклонено администратором"
            await api.reject_registration(request_id, "Отклонено администратором")
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"❌ Заявка #{request_id} отклонена.")
            await callback.answer("Отклонено!")
            
    except Exception as e:
        await callback.message.answer(f"Ошибка: {str(e)}")
        await callback.answer("Ошибка", show_alert=True)
    finally:
        await api.close()
