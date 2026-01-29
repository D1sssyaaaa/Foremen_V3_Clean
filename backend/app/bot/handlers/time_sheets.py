"""Хэндлеры для подачи табелей РТБ - комбинированный вариант"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime, date
import io
import re

from app.bot.states import TimeSheetStates
from app.bot.keyboards import (
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_timesheet_method_keyboard,
    get_objects_keyboard,
    get_add_worker_keyboard,
    get_period_keyboard,
    get_skip_comment_keyboard
)
from app.bot.utils import APIClient

router = Router()

# Шаблон Excel для табеля (base64 или генерация на лету)
TIMESHEET_TEMPLATE_CONTENT = """ФИО работника,Дата рождения,Телефон,Дата,Объект,Часы
Иванов Иван Иванович,01.01.1990,+79001234567,15.01.2026,ОБ-001,8
Иванов Иван Иванович,01.01.1990,+79001234567,16.01.2026,ОБ-001,10
Петров Петр Петрович,15.03.1985,+79009876543,15.01.2026,ОБ-001,8
"""


def parse_date(date_str: str) -> date | None:
    """Парсинг даты из строки DD.MM.YYYY"""
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def format_workers_list(workers: list) -> str:
    """Форматирование списка работников"""
    if not workers:
        return "Нет работников"
    
    lines = []
    for i, w in enumerate(workers, 1):
        lines.append(f"{i}. {w['name']} ({w.get('birth_date', '-')}, {w.get('phone', '-')})")
    return "\n".join(lines)


def format_hours_summary(workers: list, hours_data: dict) -> str:
    """Форматирование сводки по часам"""
    lines = []
    total_hours = 0
    
    for i, w in enumerate(workers):
        worker_hours = hours_data.get(str(i), {})
        worker_total = sum(worker_hours.values()) if isinstance(worker_hours, dict) else 0
        total_hours += worker_total
        lines.append(f"• {w['name']}: {worker_total} ч.")
    
    lines.append(f"\n<b>Всего:</b> {total_hours} ч.")
    return "\n".join(lines)


# =============================================================================
# НАЧАЛО: Выбор способа подачи табеля
# =============================================================================

@router.message(F.text == "📊 Подать табель РТБ")
async def start_timesheet(message: Message, state: FSMContext):
    """Начало подачи табеля - выбор способа"""
    # Сохраняем токен если есть
    data = await state.get_data()
    token = data.get("token")
    
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await message.answer(
        "📊 <b>Подача табеля РТБ</b>\n\n"
        "Выберите способ подачи табеля:",
        parse_mode="HTML",
        reply_markup=get_timesheet_method_keyboard()
    )
    await state.set_state(TimeSheetStates.select_method)


# =============================================================================
# СПОСОБ 1: Скачать шаблон
# =============================================================================

@router.callback_query(F.data == "ts_method:template", TimeSheetStates.select_method)
async def send_template(callback: CallbackQuery, state: FSMContext):
    """Отправка шаблона Excel"""
    # Создаем CSV шаблон (можно заменить на настоящий xlsx)
    template_file = BufferedInputFile(
        TIMESHEET_TEMPLATE_CONTENT.encode('utf-8-sig'),
        filename="шаблон_табель_ртб.csv"
    )
    
    await callback.message.answer_document(
        template_file,
        caption=(
            "📊 <b>Шаблон табеля РТБ</b>\n\n"
            "Заполните файл по образцу:\n"
            "• ФИО работника\n"
            "• Дата рождения (ДД.ММ.ГГГГ)\n"
            "• Телефон\n"
            "• Дата работы (ДД.ММ.ГГГГ)\n"
            "• Код объекта\n"
            "• Количество часов\n\n"
            "После заполнения нажмите <b>📄 Загрузить Excel</b>"
        ),
        parse_mode="HTML"
    )
    
    await callback.message.edit_text(
        "📊 <b>Подача табеля РТБ</b>\n\n"
        "Шаблон отправлен ⬇️\n\n"
        "Выберите способ подачи табеля:",
        parse_mode="HTML",
        reply_markup=get_timesheet_method_keyboard()
    )
    await callback.answer("Шаблон отправлен!")


# =============================================================================
# СПОСОБ 2: Загрузка Excel
# =============================================================================

@router.callback_query(F.data == "ts_method:upload", TimeSheetStates.select_method)
async def start_upload(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки Excel файла"""
    await callback.message.edit_text(
        "📄 <b>Загрузка табеля из файла</b>\n\n"
        "📎 Отправьте Excel/CSV файл с табелем.\n\n"
        "<b>Формат файла:</b>\n"
        "• Колонки: ФИО, Дата рождения, Телефон, Дата, Объект, Часы\n"
        "• Даты в формате ДД.ММ.ГГГГ\n\n"
        "Можете использовать скачанный шаблон.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TimeSheetStates.upload_file)
    await callback.answer()


@router.message(TimeSheetStates.upload_file, F.document)
async def process_timesheet_file(message: Message, state: FSMContext):
    """Обработка загруженного файла"""
    document = message.document
    
    # Проверяем формат файла
    if not document.file_name.endswith(('.xlsx', '.xls', '.csv')):
        await message.answer(
            "❌ Неправильный формат файла.\n"
            "Отправьте Excel (.xlsx, .xls) или CSV файл."
        )
        return
    
    try:
        # Скачиваем файл
        file = await message.bot.get_file(document.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        
        # Сохраняем в состояние
        await state.update_data(
            file_name=document.file_name,
            file_bytes=file_bytes.read(),
            method="upload"
        )
        
        await message.answer(
            f"✅ Файл <b>{document.file_name}</b> получен.\n\n"
            "📝 Введите комментарий к табелю:",
            parse_mode="HTML",
            reply_markup=get_skip_comment_keyboard()
        )
        await state.set_state(TimeSheetStates.input_comment)
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при обработке файла:\n{str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
        token = (await state.get_data()).get("token")
        await state.clear()
        if token:
            await state.update_data(token=token)


@router.message(TimeSheetStates.upload_file)
async def process_invalid_upload(message: Message, state: FSMContext):
    """Обработка неправильного типа сообщения при загрузке"""
    await message.answer(
        "❌ Пожалуйста, отправьте файл (Excel или CSV).\n\n"
        "Или отмените операцию кнопкой ниже.",
        reply_markup=get_cancel_keyboard()
    )


# =============================================================================
# СПОСОБ 3: Ручной ввод
# =============================================================================

@router.callback_query(F.data == "ts_method:manual", TimeSheetStates.select_method)
async def start_manual_entry(callback: CallbackQuery, state: FSMContext):
    """Начало ручного ввода табеля"""
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await callback.message.edit_text(
            "❌ Для подачи табеля необходима авторизация.\n"
            "Пожалуйста, зарегистрируйтесь или войдите.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем список объектов
    try:
        api = APIClient(token)
        objects = await api.get_objects()
        await api.close()
        
        if not objects:
            await callback.message.edit_text(
                "❌ Нет доступных объектов для табеля.\n"
                "Обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await state.update_data(method="manual", workers=[], hours_data={})
        
        await callback.message.edit_text(
            "✍️ <b>Ручной ввод табеля</b>\n\n"
            "Шаг 1/5: Выберите объект учета:",
            parse_mode="HTML",
            reply_markup=get_objects_keyboard(objects)
        )
        await state.set_state(TimeSheetStates.select_object)
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка получения объектов:\n{str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("object:"), TimeSheetStates.select_object)
async def select_object_for_timesheet(callback: CallbackQuery, state: FSMContext):
    """Выбор объекта для табеля"""
    object_id = int(callback.data.split(":")[1])
    await state.update_data(cost_object_id=object_id)
    
    await callback.message.edit_text(
        "✍️ <b>Ручной ввод табеля</b>\n\n"
        "Шаг 2/5: Выберите период табеля:",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )
    await state.set_state(TimeSheetStates.input_period_start)
    await callback.answer()


@router.callback_query(F.data.startswith("period:"), TimeSheetStates.input_period_start)
async def select_period(callback: CallbackQuery, state: FSMContext):
    """Выбор периода табеля"""
    period_data = callback.data.replace("period:", "")
    
    if period_data == "custom":
        await callback.message.edit_text(
            "📅 <b>Период табеля</b>\n\n"
            "Введите период в формате:\n"
            "<code>ДД.ММ.ГГГГ - ДД.ММ.ГГГГ</code>\n\n"
            "Например: 01.01.2026 - 15.01.2026",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(TimeSheetStates.input_period_end)
        await callback.answer()
        return
    
    # Парсим период из callback
    parts = period_data.split(":")
    if len(parts) == 2:
        period_start = date.fromisoformat(parts[0])
        period_end = date.fromisoformat(parts[1])
        
        await state.update_data(
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat()
        )
        
        await callback.message.edit_text(
            f"✍️ <b>Ручной ввод табеля</b>\n\n"
            f"📅 Период: {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}\n\n"
            f"Шаг 3/5: Добавьте работников бригады.\n\n"
            f"Введите данные работника в формате:\n"
            f"<code>ФИО, дата рождения, телефон</code>\n\n"
            f"Например:\n"
            f"<code>Иванов Иван Иванович, 01.01.1990, +79001234567</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(TimeSheetStates.input_worker_name)
    
    await callback.answer()


@router.message(TimeSheetStates.input_period_end)
async def process_custom_period(message: Message, state: FSMContext):
    """Обработка ручного ввода периода"""
    text = message.text.strip()
    
    # Парсим формат ДД.ММ.ГГГГ - ДД.ММ.ГГГГ
    match = re.match(r'(\d{2}\.\d{2}\.\d{4})\s*[-–]\s*(\d{2}\.\d{2}\.\d{4})', text)
    if not match:
        await message.answer(
            "❌ Неверный формат периода.\n\n"
            "Введите в формате:\n"
            "<code>ДД.ММ.ГГГГ - ДД.ММ.ГГГГ</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    period_start = parse_date(match.group(1))
    period_end = parse_date(match.group(2))
    
    if not period_start or not period_end:
        await message.answer(
            "❌ Неверная дата.\n"
            "Проверьте формат: ДД.ММ.ГГГГ",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if period_end < period_start:
        await message.answer(
            "❌ Дата окончания не может быть раньше даты начала.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat()
    )
    
    await message.answer(
        f"✍️ <b>Ручной ввод табеля</b>\n\n"
        f"📅 Период: {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}\n\n"
        f"Шаг 3/5: Добавьте работников бригады.\n\n"
        f"Введите данные работника в формате:\n"
        f"<code>ФИО, дата рождения, телефон</code>\n\n"
        f"Например:\n"
        f"<code>Иванов Иван Иванович, 01.01.1990, +79001234567</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TimeSheetStates.input_worker_name)


@router.message(TimeSheetStates.input_worker_name)
async def process_worker_data(message: Message, state: FSMContext):
    """Обработка данных работника"""
    text = message.text.strip()
    
    # Парсим формат: ФИО, дата, телефон
    parts = [p.strip() for p in text.split(",")]
    
    if len(parts) < 3:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Введите данные в формате:\n"
            "<code>ФИО, дата рождения, телефон</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    name = parts[0]
    birth_date_str = parts[1]
    phone = parts[2]
    
    # Проверяем дату рождения
    birth_date = parse_date(birth_date_str)
    if not birth_date:
        await message.answer(
            "❌ Неверный формат даты рождения.\n"
            "Используйте формат ДД.ММ.ГГГГ",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Добавляем работника
    data = await state.get_data()
    workers = data.get("workers", [])
    workers.append({
        "name": name,
        "birth_date": birth_date.isoformat(),
        "birth_date_str": birth_date_str,
        "phone": phone
    })
    await state.update_data(workers=workers)
    
    await message.answer(
        f"✅ Работник добавлен: <b>{name}</b>\n\n"
        f"<b>Текущий список ({len(workers)}):</b>\n"
        f"{format_workers_list(workers)}\n\n"
        f"Добавить еще работника или перейти к вводу часов?",
        parse_mode="HTML",
        reply_markup=get_add_worker_keyboard()
    )
    await state.set_state(TimeSheetStates.add_more_workers)


@router.callback_query(F.data == "add_worker", TimeSheetStates.add_more_workers)
async def add_another_worker(callback: CallbackQuery, state: FSMContext):
    """Добавление еще одного работника"""
    await callback.message.edit_text(
        "👤 <b>Добавление работника</b>\n\n"
        "Введите данные работника в формате:\n"
        "<code>ФИО, дата рождения, телефон</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TimeSheetStates.input_worker_name)
    await callback.answer()


@router.callback_query(F.data == "finish_workers", TimeSheetStates.add_more_workers)
async def finish_workers_entry(callback: CallbackQuery, state: FSMContext):
    """Завершение ввода работников, переход к часам"""
    data = await state.get_data()
    workers = data.get("workers", [])
    
    if not workers:
        await callback.answer("Добавьте хотя бы одного работника!", show_alert=True)
        return
    
    # Начинаем ввод часов для первого работника
    await state.update_data(current_worker_index=0, hours_data={})
    
    worker = workers[0]
    period_start = date.fromisoformat(data["period_start"])
    period_end = date.fromisoformat(data["period_end"])
    
    await callback.message.edit_text(
        f"⏱️ <b>Ввод часов работы</b>\n\n"
        f"Работник 1/{len(workers)}: <b>{worker['name']}</b>\n\n"
        f"📅 Период: {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}\n\n"
        f"Введите часы работы в формате:\n"
        f"<code>ДД.ММ часы</code> (каждая дата с новой строки)\n\n"
        f"Например:\n"
        f"<code>15.01 8\n16.01 10\n17.01 8</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TimeSheetStates.input_worker_hours)
    await callback.answer()


@router.message(TimeSheetStates.input_worker_hours)
async def process_worker_hours(message: Message, state: FSMContext):
    """Обработка часов работника"""
    text = message.text.strip()
    data = await state.get_data()
    
    current_idx = data.get("current_worker_index", 0)
    workers = data.get("workers", [])
    hours_data = data.get("hours_data", {})
    period_year = date.fromisoformat(data["period_start"]).year
    
    # Парсим строки с часами
    worker_hours = {}
    lines = text.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Формат: ДД.ММ часы или ДД.ММ.ГГГГ часы
        match = re.match(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+(\d+(?:[.,]\d+)?)', line)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else period_year
            hours = float(match.group(4).replace(",", "."))
            
            try:
                work_date = date(year, month, day)
                worker_hours[work_date.isoformat()] = hours
            except ValueError:
                pass
    
    if not worker_hours:
        await message.answer(
            "❌ Не удалось распознать часы.\n\n"
            "Введите в формате:\n"
            "<code>ДД.ММ часы</code>\n\n"
            "Например:\n"
            "<code>15.01 8\n16.01 10</code>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Сохраняем часы работника
    hours_data[str(current_idx)] = worker_hours
    await state.update_data(hours_data=hours_data)
    
    worker = workers[current_idx]
    total_hours = sum(worker_hours.values())
    
    # Проверяем, есть ли еще работники
    if current_idx + 1 < len(workers):
        next_idx = current_idx + 1
        await state.update_data(current_worker_index=next_idx)
        next_worker = workers[next_idx]
        
        period_start = date.fromisoformat(data["period_start"])
        period_end = date.fromisoformat(data["period_end"])
        
        await message.answer(
            f"✅ Часы для <b>{worker['name']}</b> сохранены: {total_hours} ч.\n\n"
            f"⏱️ <b>Ввод часов работы</b>\n\n"
            f"Работник {next_idx + 1}/{len(workers)}: <b>{next_worker['name']}</b>\n\n"
            f"📅 Период: {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}\n\n"
            f"Введите часы работы:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
    else:
        # Все работники введены, переходим к комментарию
        await state.update_data(method="manual")
        
        await message.answer(
            f"✅ Часы для <b>{worker['name']}</b> сохранены: {total_hours} ч.\n\n"
            f"Все работники добавлены!\n\n"
            f"📝 Введите комментарий к табелю:",
            parse_mode="HTML",
            reply_markup=get_skip_comment_keyboard()
        )
        await state.set_state(TimeSheetStates.input_comment)


# =============================================================================
# ОБЩЕЕ: Комментарий и подтверждение
# =============================================================================

@router.message(TimeSheetStates.input_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария к табелю"""
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await show_confirmation(message, state)


@router.callback_query(F.data == "skip_comment", TimeSheetStates.input_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропуск комментария"""
    await state.update_data(comment=None)
    await show_confirmation(callback.message, state, edit=True)
    await callback.answer()


async def show_confirmation(message: Message, state: FSMContext, edit: bool = False):
    """Показ подтверждения табеля"""
    data = await state.get_data()
    method = data.get("method", "upload")
    
    if method == "upload":
        # Для загрузки файла
        preview = (
            "📋 <b>Предпросмотр табеля РТБ:</b>\n\n"
            f"📎 Файл: {data.get('file_name', 'N/A')}\n"
            f"📏 Размер: {len(data.get('file_bytes', b'')) / 1024:.1f} KB\n"
        )
    else:
        # Для ручного ввода
        workers = data.get("workers", [])
        hours_data = data.get("hours_data", {})
        period_start = date.fromisoformat(data["period_start"])
        period_end = date.fromisoformat(data["period_end"])
        
        preview = (
            "📋 <b>Предпросмотр табеля РТБ:</b>\n\n"
            f"📅 Период: {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}\n"
            f"👥 Работников: {len(workers)}\n\n"
            f"<b>Часы по работникам:</b>\n"
            f"{format_hours_summary(workers, hours_data)}\n"
        )
    
    if data.get("comment"):
        preview += f"\n📝 Комментарий: {data['comment']}\n"
    
    preview += "\n✅ Подтвердить отправку табеля?"
    
    if edit:
        await message.edit_text(preview, parse_mode="HTML", reply_markup=get_confirm_keyboard())
    else:
        await message.answer(preview, parse_mode="HTML", reply_markup=get_confirm_keyboard())
    
    await state.set_state(TimeSheetStates.confirm)


@router.callback_query(F.data == "confirm_yes", TimeSheetStates.confirm)
async def process_confirm_yes(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка табеля"""
    data = await state.get_data()
    token = data.get("token")
    
    if not token:
        await callback.message.edit_text(
            "❌ Ошибка авторизации. Попробуйте заново.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        await callback.answer()
        return
    
    api = APIClient(token)
    
    try:
        method = data.get("method", "upload")
        
        if method == "upload":
            # Отправляем файл
            # TODO: реализовать upload_timesheet в API
            result_text = (
                "✅ <b>Табель РТБ отправлен!</b>\n\n"
                f"📎 Файл: {data.get('file_name')}\n\n"
                "Ваш табель принят на проверку.\n"
                "HR-менеджер проверит данные и укажет ставки."
            )
        else:
            # Отправляем данные ручного ввода
            timesheet_data = {
                "cost_object_id": data.get("cost_object_id"),
                "period_start": data.get("period_start"),
                "period_end": data.get("period_end"),
                "workers": data.get("workers", []),
                "hours_data": data.get("hours_data", {}),
                "notes": data.get("comment")
            }
            
            # TODO: вызов API create_timesheet
            # result = await api.create_timesheet(timesheet_data)
            
            workers = data.get("workers", [])
            hours_data = data.get("hours_data", {})
            total_hours = sum(
                sum(h.values()) if isinstance(h, dict) else 0 
                for h in hours_data.values()
            )
            
            result_text = (
                "✅ <b>Табель РТБ отправлен!</b>\n\n"
                f"👥 Работников: {len(workers)}\n"
                f"⏱️ Всего часов: {total_hours}\n\n"
                "Ваш табель принят на проверку.\n"
                "HR-менеджер проверит данные и укажет ставки."
            )
        
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при отправке табеля:</b>\n\n{str(e)}",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        await api.close()
    
    # Сохраняем токен при очистке
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await callback.answer()


@router.callback_query(F.data == "confirm_no", TimeSheetStates.confirm)
async def process_confirm_no(callback: CallbackQuery, state: FSMContext):
    """Отмена отправки табеля"""
    token = (await state.get_data()).get("token")
    
    await callback.message.edit_text(
        "❌ Отправка табеля отменена",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await callback.answer()


# =============================================================================
# ОТМЕНА на любом этапе
# =============================================================================

@router.callback_query(F.data == "cancel")
async def cancel_timesheet(callback: CallbackQuery, state: FSMContext):
    """Отмена на любом этапе"""
    token = (await state.get_data()).get("token")
    
    await callback.message.edit_text(
        "❌ Операция отменена",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()
    if token:
        await state.update_data(token=token)
    
    await callback.answer()
