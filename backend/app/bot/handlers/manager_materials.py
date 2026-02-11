from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.utils.api_client import APIClient
from app.bot.states import MaterialRequestStates

router = Router()

@router.message(F.text == "📋 Активные заявки")
async def show_active_requests(message: Message, state: FSMContext):
    """Показать список активных заявок (для Менеджера)"""
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await message.answer("❌ Ошибка авторизации. Введите /start")
        return

    api = APIClient(token)
    try:
        # Получаем список заявок со статусом NEW (или всеми активными)
        # TODO: Реализовать фильтрацию в API
        requests = await api.get_material_requests(status="NEW") 
        
        if not requests:
            await message.answer("📭 Новых заявок нет.")
            return
            
        await message.answer(f"📋 Найдено {len(requests)} новых заявок:")
        
        for req in requests:
            # Формируем краткую карточку
            text = (
                f"🆕 <b>Заявка #{req['id']}</b>\n"
                f"🏗 Объект: {req.get('cost_object', {}).get('name', '???')}\n"
                f"📅 Дата: {req.get('date_needed')}\n"
                f"📦 Позиций: {len(req.get('items', []))}\n"
            )
            
            # Инлайн кнопки действий
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👁 Просмотр", callback_data=f"mat_mgr:view:{req['id']}"),
                    InlineKeyboardButton(text="✅ В работу", callback_data=f"mat_mgr:approve:{req['id']}")
                ]
            ])
            
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке заявок: {str(e)}")
    finally:
        await api.close()

@router.callback_query(F.data.startswith("mat_mgr:view:"))
async def view_request_details(callback: CallbackQuery, state: FSMContext):
    """Просмотр деталей заявки"""
    req_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    token = data.get("token")
    
    api = APIClient(token)
    try:
        req = await api.get_material_request(req_id)
        
        # Формируем полный текст
        items_text = "\n".join([
            f"- {item['name']}: {item['quantity']} {item['unit']}" 
            for item in req.get('items', [])
        ])
        
        text = (
            f"📦 <b>Заявка #{req['id']}</b>\n"
            f"🏗 Объект: {req.get('cost_object', {}).get('name')}\n"
            f"👤 Автор: {req.get('author', {}).get('full_name')}\n"
            f"📅 Дата поставки: {req.get('date_needed')}\n"
            f"priority: {req.get('urgency')}\n\n"
            f"📋 <b>Материалы:</b>\n"
            f"{items_text}\n"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ В работу", callback_data=f"mat_mgr:approve:{req['id']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mat_mgr:reject:{req['id']}")
            ],
            [InlineKeyboardButton(text="🔙 Скрыть", callback_data="hide")]
        ])
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    finally:
        await api.close()

@router.callback_query(F.data.startswith("mat_mgr:approve:"))
async def approve_request(callback: CallbackQuery, state: FSMContext):
    """Перевод заявки в статус IN_PROGRESS"""
    req_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    token = data.get("token")
    
    api = APIClient(token)
    try:
        # Обновляем статус
        # TODO: Добавить метод update_status в APIClient
        await api.update_material_request_status(req_id, "IN_PROGRESS")
        
        await callback.message.edit_text(
            f"✅ Заявка #{req_id} принята в работу!",
            reply_markup=None
        )
        await callback.answer("Статус обновлен")
        
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    finally:
        await api.close()

@router.callback_query(F.data.startswith("mat_mgr:reject:"))
async def reject_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало отклонения заявки (запрос причины)"""
    req_id = int(callback.data.split(":")[2])
    
    # Сохраняем ID заявки в состояние
    await state.update_data(rejecting_request_id=req_id)
    await state.set_state(MaterialRequestStates.manager_reject_reason)
    
    await callback.message.answer(
        f"✍️ Укажите причину отклонения заявки #{req_id}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reject")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_reject", StateFilter(MaterialRequestStates.manager_reject_reason))
async def cancel_reject(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await callback.message.delete()
    await callback.answer("Отменено")

@router.message(StateFilter(MaterialRequestStates.manager_reject_reason))
async def process_reject_reason(message: Message, state: FSMContext):
    """Обработка ввода причины отклонения"""
    data = await state.get_data()
    req_id = data.get("rejecting_request_id")
    token = data.get("token")
    reason = message.text
    
    api = APIClient(token)
    try:
        await api.update_material_request_status(req_id, "REJECTED", reason=reason)
        await message.answer(f"❌ Заявка #{req_id} отклонена.\nПричина: {reason}")
        await state.set_state(None)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    finally:
        await api.close()
