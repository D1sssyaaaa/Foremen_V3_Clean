from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.utils.api_client import APIClient
from app.bot.states import EquipmentOrderStates

router = Router()

@router.message(F.text == "📋 Новые заявки")
async def show_new_equipment_requests(message: Message, state: FSMContext):
    """Показать список новых заявок на технику"""
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await message.answer("❌ Ошибка авторизации. Введите /start")
        return

    api = APIClient(token)
    try:
        # TODO: Реализовать фильтрацию по статусу в API
        requests = await api.get_equipment_requests(status="NEW") 
        
        if not requests:
            await message.answer("📭 Новых заявок на технику нет.")
            return
            
        await message.answer(f"📋 Найдено {len(requests)} новых заявок:")
        
        for req in requests:
            text = (
                f"🆕 <b>Заявка на технику #{req['id']}</b>\n"
                f"🏗 Объект: {req.get('cost_object', {}).get('name', '???')}\n"
                f"🚜 Тип: {req.get('equipment_type')}\n"
                f"📅 C: {req.get('start_date')} по {req.get('end_date')}\n"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"eq_mgr:approve:{req['id']}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"eq_mgr:reject:{req['id']}")
                ]
            ])
            
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке заявок: {str(e)}")
    finally:
        await api.close()

@router.callback_query(F.data.startswith("eq_mgr:approve:"))
async def approve_equipment_request(callback: CallbackQuery, state: FSMContext):
    """Одобрение заявки (без ввода номера, просто статус APPROVED)"""
    req_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    token = data.get("token")
    
    api = APIClient(token)
    try:
        # Ставим статус APPROVED. 
        # TODO: Добавить метод в APIClient
        await api.update_equipment_request_status(req_id, "APPROVED")
        
        await callback.message.edit_text(
            f"✅ Заявка #{req_id} одобрена! Уведомление отправлено прорабу.",
            reply_markup=None
        )
        await callback.answer("Одобрено")
        
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    finally:
        await api.close()

@router.callback_query(F.data.startswith("eq_mgr:reject:"))
async def reject_equipment_start(callback: CallbackQuery, state: FSMContext):
    """Отклонить заявку (запрос причины)"""
    req_id = int(callback.data.split(":")[2])
    
    await state.update_data(rejecting_eq_id=req_id)
    await state.set_state(EquipmentOrderStates.manager_reject_reason)
    
    await callback.message.answer(
        f"✍️ Укажите причину отклонения заявки #{req_id}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reject")]
        ])
    )
    await callback.answer()

@router.message(StateFilter(EquipmentOrderStates.manager_reject_reason))
async def process_equipment_reject_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    req_id = data.get("rejecting_eq_id")
    token = data.get("token")
    reason = message.text
    
    api = APIClient(token)
    try:
        await api.update_equipment_request_status(req_id, "REJECTED", reason=reason)
        await message.answer(f"❌ Заявка #{req_id} отклонена.")
        await state.set_state(None)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    finally:
        await api.close()

@router.message(F.text == "✅ Активная техника")
async def show_active_equipment(message: Message, state: FSMContext):
    """Показать активную технику (статус APPROVED)"""
    data = await state.get_data()
    token = data.get("token")
    api = APIClient(token)
    try:
        requests = await api.get_equipment_requests(status="APPROVED")
        
        if not requests:
            await message.answer("Нет активной техники.")
            return
            
        await message.answer(f"🚜 В работе: {len(requests)} ед.")
        
        for req in requests:
            text = (
                f"🚜 <b>Заявка #{req['id']}</b>\n"
                f"🏗 {req.get('cost_object', {}).get('name')}\n"
                f"Тип: {req.get('equipment_type')}\n"
                f"📅 До: {req.get('end_date')}\n"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏁 Завершить работы", callback_data=f"eq_mgr:finish:{req['id']}")]
            ])
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    finally:
        await api.close()

@router.callback_query(F.data.startswith("eq_mgr:finish:"))
async def finish_equipment_work(callback: CallbackQuery, state: FSMContext):
    """Завершение работ менеджером -> Триггер сбора часов у Прораба"""
    req_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    token = data.get("token")
    
    api = APIClient(token)
    try:
        # Меняем статус на COMPLETED (или WORK_DONE, чтобы ждать часы)
        # В текущей схеме можно сразу COMPLETED, но нам нужно чтобы бот запросил часы у прораба.
        # Это должно происходить через Notification Worker, который увидит смену статуса
        # и отправит сообщение прорабу.
        
        await api.update_equipment_request_status(req_id, "COMPLETED")
        
        await callback.message.edit_text(
            f"🏁 Работы по заявке #{req_id} завершены.\n"
            "Прорабу отправлено уведомление о необходимости подать часы.",
            reply_markup=None
        )
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    finally:
        await api.close()
