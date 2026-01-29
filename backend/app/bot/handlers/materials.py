"""Хэндлеры для создания заявок на материалы (включая инертные)"""
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from app.bot.states import MaterialRequestStates
from app.bot.keyboards import (
    get_material_type_keyboard,
    get_urgency_keyboard,
    get_add_more_keyboard,
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_objects_keyboard,
    get_date_selection_keyboard,
    get_skip_comment_keyboard
)
from app.bot.utils import APIClient

router = Router()


def parse_material_input(text: str) -> dict | None:
    """
    Парсинг строки материала в формате: "Название количество единица"
    Примеры: 
        "Песок 10 т", "Цемент М500 50 кг", "Доска 100х50 20 шт"
        "песок 10м3", "кабель 3х2.5 100м", "Кирпич 434шт"
        "Кабель - 100м", "муфты АСБЛ 150/240 200 шт"
    
    Возвращает dict с ключами: material_name, quantity, unit
    Или dict с ключом error если не удалось распарсить
    """
    original_text = text
    text = text.strip()
    if not text:
        return {"error": "Пустая строка", "original": original_text}
    
    # Убираем дефис-разделитель если есть: "Кабель - 100м" -> "Кабель 100м"
    text = re.sub(r'\s*-\s*', ' ', text)
    
    # Стратегия 1: Ищем ПОСЛЕДНЕЕ число + единица в конце строки
    # Примеры: "Кабель 3х2.5 100м" -> 100м, "Муфты 150/240 200шт" -> 200шт
    pattern_with_unit = r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*([а-яА-Яa-zA-Z²³]+)$'
    match = re.match(pattern_with_unit, text)
    
    if match:
        name = match.group(1).strip()
        quantity_str = match.group(2).replace(',', '.')
        unit_raw = match.group(3).strip()
    else:
        # Стратегия 2: Ищем ПОСЛЕДНЕЕ число без явной единицы
        # Примеры: "Кабель 100", "Песок 50"
        pattern_no_unit = r'^(.+?)\s+(\d+(?:[.,]\d+)?)$'
        match = re.match(pattern_no_unit, text)
        
        if not match:
            return {
                "error": "Не найдено количество в конце строки",
                "original": original_text,
                "cleaned": text
            }
        
        name = match.group(1).strip()
        quantity_str = match.group(2).replace(',', '.')
        unit_raw = 'шт'  # по умолчанию
    
    # Нормализация единиц измерения
    unit_lower = unit_raw.lower()
    unit_map = {
        'м3': 'м³', 'м2': 'м²', 'куб': 'м³', 'кв': 'м²',
        'кубов': 'м³', 'квадратов': 'м²', 'метров': 'м',
        'штук': 'шт', 'штуки': 'шт', 'килограмм': 'кг',
        'тонн': 'т', 'тонны': 'т', 'литров': 'л', 'литр': 'л'
    }
    unit = unit_map.get(unit_lower, unit_raw)
    
    try:
        quantity = float(quantity_str)
        if quantity <= 0:
            return {
                "error": f"Количество должно быть > 0, получено: {quantity}",
                "original": original_text
            }
    except ValueError:
        return {
            "error": f"Не удалось преобразовать '{quantity_str}' в число",
            "original": original_text
        }
    
    return {
        "material_name": name,
        "quantity": quantity,
        "unit": unit
    }


def parse_materials_multiline(text: str) -> tuple[list[dict], list[str]]:
    """
    Парсинг многострочного ввода материалов.
    Возвращает (список успешных, список ошибок)
    """
    lines = text.strip().split('\n')
    success = []
    errors = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parsed = parse_material_input(line)
        if parsed and "material_name" in parsed:
            success.append(parsed)
        else:
            error_msg = parsed.get("error", "Неизвестная ошибка") if parsed else "Не распознано"
            errors.append(f"'{line}' - {error_msg}")
    
    return success, errors


@router.message(F.text == "📦 Заявка на материалы")
async def start_material_request(message: Message, state: FSMContext):
    """Начало создания заявки на материалы"""
    # Получаем токен из состояния СНАЧАЛА
    data = await state.get_data()
    token = data.get('token')
    
    # Инициализация данных заявки (сохраняем токен!)
    await state.update_data(items=[], token=token)
    
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
            "🏗️ <b>Создание заявки на материалы</b>\n\n"
            "Выберите объект учета:",
            parse_mode="HTML",
            reply_markup=get_objects_keyboard(objects)
        )
        await state.set_state(MaterialRequestStates.select_object)
    except Exception as e:
        await api.close()
        await message.answer(
            f"❌ Ошибка при загрузке объектов: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(F.data.startswith("object:"), MaterialRequestStates.select_object)
async def process_select_object(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора объекта через кнопку"""
    object_id = int(callback.data.split(":")[1])
    await state.update_data(cost_object_id=object_id)
    await callback.answer()
    
    await callback.message.edit_text(
        "📦 <b>Выберите тип материалов:</b>\n\n"
        "🏗️ <b>Обычные:</b> кирпич, цемент, гвозди, доски и т.д.\n"
        "🪨 <b>Инертные:</b> песок, щебень, ПГС, раствор (требуется время доставки)",
        parse_mode="HTML",
        reply_markup=get_material_type_keyboard()
    )
    await state.set_state(MaterialRequestStates.select_material_type)


@router.callback_query(F.data.startswith("mattype:"), MaterialRequestStates.select_material_type)
async def process_material_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа материала"""
    material_type = callback.data.split(":")[1]
    await state.update_data(material_type=material_type)
    await callback.answer()
    
    if material_type == "inert":
        # Для инертных материалов ОБЯЗАТЕЛЬНО время доставки
        await callback.message.edit_text(
            "🪨 <b>Инертные материалы</b>\n\n"
            "⚠️ Для инертных материалов обязательно указать желаемое время доставки.\n\n"
            "Введите время доставки в формате:\n"
            "• <code>08:00-12:00</code>\n"
            "• <code>14:00-18:00</code>\n"
            "• <code>утро</code> / <code>день</code> / <code>вечер</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(MaterialRequestStates.input_delivery_time)
    else:
        # Для обычных переходим к срочности
        await callback.message.edit_text(
            "🏗️ <b>Обычные материалы</b>\n\n"
            "Выберите срочность заявки:",
            parse_mode="HTML",
            reply_markup=get_urgency_keyboard()
        )
        await state.set_state(MaterialRequestStates.select_urgency)


@router.message(MaterialRequestStates.input_delivery_time)
async def process_delivery_time(message: Message, state: FSMContext):
    """Обработка времени доставки для инертных"""
    delivery_time = message.text.strip()
    
    # Базовая валидация
    if len(delivery_time) < 3:
        await message.answer(
            "❌ Время доставки слишком короткое.\n\n"
            "Примеры правильного формата:\n"
            "• 08:00-12:00\n"
            "• утро\n"
            "• с 9 до 17"
        )
        return
    
    await state.update_data(delivery_time=delivery_time)
    
    await message.answer(
        f"✅ Время доставки: <b>{delivery_time}</b>\n\n"
        "Выберите срочность заявки:",
        parse_mode="HTML",
        reply_markup=get_urgency_keyboard()
    )
    await state.set_state(MaterialRequestStates.select_urgency)


@router.callback_query(F.data.startswith("urgency:"), MaterialRequestStates.select_urgency)
async def process_urgency(callback: CallbackQuery, state: FSMContext):
    """Обработка срочности"""
    urgency = callback.data.split(":")[1]
    await state.update_data(urgency=urgency)
    await callback.answer()
    
    urgency_labels = {
        "normal": "🟢 Обычная",
        "urgent": "🟡 Срочная",
        "critical": "🔴 Критичная"
    }
    
    await callback.message.edit_text(
        f"Срочность: {urgency_labels[urgency]}\n\n"
        "📅 <b>Выберите дату поставки:</b>",
        parse_mode="HTML",
        reply_markup=get_date_selection_keyboard()
    )
    await state.set_state(MaterialRequestStates.input_required_date)


@router.callback_query(F.data.startswith("date:"), MaterialRequestStates.input_required_date)
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты через кнопку"""
    date_value = callback.data.split(":")[1]
    await callback.answer()
    
    if date_value == "custom":
        # Ручной ввод даты
        await callback.message.edit_text(
            "📅 <b>Введите дату поставки</b>\n\n"
            "Формат: <code>ДД.ММ.ГГГГ</code>\n"
            "Например: <code>05.02.2026</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(MaterialRequestStates.input_custom_date)
        return
    
    # Дата выбрана из кнопок
    date_obj = datetime.fromisoformat(date_value).date()
    await state.update_data(required_date=date_obj.isoformat())
    
    await callback.message.edit_text(
        f"✅ Дата поставки: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
        "📝 <b>Добавьте позиции материалов</b>\n\n"
        "Введите материал в формате:\n"
        "<code>Название количество единица</code>\n\n"
        "Примеры инертных материалов:\n"
        "• <code>Песок 10 т</code>\n"
        "• <code>Щебень фр.20-40 15 т</code>\n"
        "• <code>ПГС 8 т</code>\n"
        "• <code>Раствор М150 3 м³</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(MaterialRequestStates.input_material_item)


@router.message(MaterialRequestStates.input_custom_date)
async def process_custom_date(message: Message, state: FSMContext):
    """Обработка ручного ввода даты"""
    try:
        date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        
        # Проверка что дата в будущем или сегодня
        if date_obj < datetime.now().date():
            await message.answer(
                "❌ Дата должна быть сегодня или в будущем.\n"
                "Введите корректную дату:"
            )
            return
        
        await state.update_data(required_date=date_obj.isoformat())
        
        await message.answer(
            f"✅ Дата поставки: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
            "📝 <b>Добавьте позиции материалов</b>\n\n"
            "Введите материал в формате:\n"
            "<code>Название количество единица</code>\n\n"
            "Примеры инертных материалов:\n"
            "• <code>Песок 10 т</code>\n"
            "• <code>Щебень фр.20-40 15 т</code>\n"
            "• <code>ПГС 8 т</code>\n"
            "• <code>Раствор М150 3 м³</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(MaterialRequestStates.input_material_item)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Введите дату в формате <code>ДД.ММ.ГГГГ</code>\n"
            "Например: <code>05.02.2026</code>",
            parse_mode="HTML"
        )


@router.message(MaterialRequestStates.input_material_item)
async def process_material_item(message: Message, state: FSMContext):
    """Обработка ввода материалов (поддержка многострочного ввода)"""
    text = message.text.strip()
    
    # Проверяем, есть ли многострочный ввод
    if '\n' in text:
        # Многострочный ввод - парсим все строки
        success_items, errors = parse_materials_multiline(text)
        
        if success_items:
            # Добавляем все успешно распознанные
            data = await state.get_data()
            items = data.get("items", [])
            
            for item in success_items:
                items.append({
                    "material_name": item["material_name"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "description": None
                })
            
            await state.update_data(items=items)
            
            # Формируем сообщение
            added_list = "\n".join([
                f"• {item['material_name']} — {item['quantity']} {item['unit']}"
                for item in success_items
            ])
            
            msg = f"✅ <b>Добавлено {len(success_items)} позиций:</b>\n{added_list}\n\n"
            
            if errors:
                error_list = "\n".join(errors[:5])  # Показываем первые 5 ошибок
                msg += f"⚠️ <b>Не распознано ({len(errors)}):</b>\n{error_list}\n\n"
            
            msg += f"📦 <b>Всего позиций:</b> {len(items)}\n\nДобавьте ещё или завершите:"
            
            await message.answer(msg, parse_mode="HTML", reply_markup=get_add_more_keyboard())
            await state.set_state(MaterialRequestStates.add_material_item)
        else:
            # Ничего не распознано
            error_list = "\n".join(errors[:5])
            await message.answer(
                f"❌ <b>Не удалось распознать материалы:</b>\n{error_list}\n\n"
                f"<b>Правильный формат (каждый с новой строки):</b>\n"
                f"<code>Песок 10 т\nКирпич 500 шт\nЦемент 25 кг</code>",
                parse_mode="HTML"
            )
        return
    
    # Однострочный ввод
    parsed = parse_material_input(text)
    
    # Проверяем на ошибку парсинга
    if parsed and "error" in parsed:
        error_info = parsed
        await message.answer(
            f"❌ <b>Ошибка:</b> {error_info.get('error')}\n\n"
            f"<b>Ваш ввод:</b> <code>{text}</code>\n\n"
            f"<b>Формат:</b> <code>Название количество единица</code>\n"
            f"<b>Пример:</b> <code>Песок 10 т</code> или <code>Кирпич 500 шт</code>\n\n"
            f"💡 Можно вводить несколько материалов, каждый с новой строки!",
            parse_mode="HTML"
        )
        return
    
    if not parsed or "material_name" not in parsed:
        await message.answer(
            "❌ Не удалось распознать материал.\n\n"
            "Введите в формате: <code>Название количество единица</code>\n\n"
            "Примеры:\n"
            "• <code>Песок 10 т</code>\n"
            "• <code>Кирпич красный 500 шт</code>\n"
            "• <code>Цемент М500 2.5 т</code>",
            parse_mode="HTML"
        )
        return
    
    # Добавляем позицию
    data = await state.get_data()
    items = data.get("items", [])
    items.append({
        "material_name": parsed["material_name"],
        "quantity": parsed["quantity"],
        "unit": parsed["unit"],
        "description": None
    })
    await state.update_data(items=items)
    
    await message.answer(
        f"✅ Добавлено: <b>{parsed['material_name']}</b> — {parsed['quantity']} {parsed['unit']}\n\n"
        f"📦 Всего позиций: {len(items)}\n\n"
        "Добавьте еще материал или завершите список:",
        parse_mode="HTML",
        reply_markup=get_add_more_keyboard()
    )
    await state.set_state(MaterialRequestStates.add_material_item)


@router.callback_query(F.data == "add:more", MaterialRequestStates.add_material_item)
async def add_more_items(callback: CallbackQuery, state: FSMContext):
    """Добавить еще позицию"""
    await callback.answer()
    await callback.message.edit_text(
        "📝 Введите следующий материал:\n\n"
        "<code>Название количество единица</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(MaterialRequestStates.input_material_item)


@router.callback_query(F.data == "add:done", MaterialRequestStates.add_material_item)
async def finish_adding_items(callback: CallbackQuery, state: FSMContext):
    """Завершить добавление позиций — переход к комментарию"""
    await callback.answer()
    
    data = await state.get_data()
    items = data.get("items", [])
    
    if not items:
        await callback.message.edit_text(
            "❌ Добавьте хотя бы один материал!",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(MaterialRequestStates.input_material_item)
        return
    
    await callback.message.edit_text(
        "💬 <b>Комментарий к заявке</b>\n\n"
        "Введите комментарий или нажмите кнопку ниже:",
        parse_mode="HTML",
        reply_markup=get_skip_comment_keyboard()
    )
    await state.set_state(MaterialRequestStates.input_comment)


@router.message(MaterialRequestStates.input_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await show_request_summary(message, state)


@router.callback_query(F.data == "skip_comment", MaterialRequestStates.input_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропуск комментария"""
    await callback.answer()
    await state.update_data(comment=None)
    await show_request_summary(callback.message, state, edit=True)


async def show_request_summary(message: Message, state: FSMContext, edit: bool = False):
    """Показ сводки заявки перед отправкой"""
    data = await state.get_data()
    items = data.get("items", [])
    
    # Формирование сводки
    summary = "📋 <b>Сводка заявки:</b>\n\n"
    summary += f"🏗️ Объект: #{data['cost_object_id']}\n"
    summary += f"📦 Тип: {'🪨 Инертные' if data['material_type'] == 'inert' else '🏗️ Обычные'}\n"
    
    if data.get("delivery_time"):
        summary += f"🕐 Время доставки: {data['delivery_time']}\n"
    
    urgency_labels = {"normal": "🟢 Обычная", "urgent": "🟡 Срочная", "critical": "🔴 Критичная"}
    summary += f"⚡ Срочность: {urgency_labels[data['urgency']]}\n"
    summary += f"📅 Дата: {datetime.fromisoformat(data['required_date']).strftime('%d.%m.%Y')}\n"
    
    if data.get("comment"):
        summary += f"💬 Комментарий: {data['comment']}\n"
    
    summary += f"\n<b>Позиции ({len(items)}):</b>\n"
    for i, item in enumerate(items, 1):
        summary += f"{i}. {item['material_name']} — {item['quantity']} {item['unit']}\n"
    
    summary += "\n✅ Отправить заявку?"
    
    if edit:
        await message.edit_text(
            summary,
            parse_mode="HTML",
            reply_markup=get_confirm_keyboard()
        )
    else:
        await message.answer(
            summary,
            parse_mode="HTML",
            reply_markup=get_confirm_keyboard()
        )
    
    await state.set_state(MaterialRequestStates.confirm)


@router.callback_query(F.data == "confirm_yes", MaterialRequestStates.confirm)
async def confirm_request(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка заявки"""
    await callback.answer("⏳ Отправка заявки...")
    
    data = await state.get_data()
    token = data.get('token')
    
    # Формирование запроса к API
    request_data = {
        "cost_object_id": data["cost_object_id"],
        "material_type": data["material_type"],
        "urgency": data["urgency"],
        "expected_delivery_date": data["required_date"],
        "items": data["items"]
    }
    
    if data.get("delivery_time"):
        request_data["delivery_time"] = data["delivery_time"]
    
    if data.get("comment"):
        request_data["comment"] = data["comment"]
    
    try:
        if token:
            api = APIClient(token)
            result = await api.create_material_request(request_data)
            await api.close()
            
            request_id = result.get('id', 'N/A')
            await callback.message.edit_text(
                f"✅ <b>Заявка успешно создана!</b>\n\n"
                f"📝 Номер заявки: <code>#{request_id}</code>\n"
                f"📊 Статус: <b>Новая</b>\n\n"
                "Вы получите уведомление при изменении статуса.",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "✅ <b>Заявка создана (демо)</b>\n\n"
                "⚠️ Отправка на сервер недоступна — нет авторизации.\n"
                "Отправьте /start для авторизации.",
                parse_mode="HTML"
            )
        
        # Сохраняем токен перед очисткой
        await state.clear()
        if token:
            await state.update_data(token=token)
            
        await callback.message.answer(
            "Выберите действие из меню:",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при создании заявки:\n{str(e)}",
            parse_mode="HTML"
        )
        # Сохраняем токен
        token = data.get('token')
        await state.clear()
        if token:
            await state.update_data(token=token)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data == "confirm_no", MaterialRequestStates.confirm)
async def cancel_request(callback: CallbackQuery, state: FSMContext):
    """Отмена заявки"""
    data = await state.get_data()
    token = data.get('token')
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await callback.answer("❌ Заявка отменена")
    await callback.message.edit_text("❌ Заявка отменена.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    data = await state.get_data()
    token = data.get('token')
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await callback.answer("❌ Действие отменено")
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.message.answer(
        "Выберите действие из меню:",
        reply_markup=get_main_menu_keyboard()
    )
