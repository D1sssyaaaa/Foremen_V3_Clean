from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, WebAppInfo
from aiogram.fsm.context import FSMContext
from datetime import datetime, date
import io
import re
import json
import urllib.parse
from sqlalchemy.future import select

from app.bot.states import TimeSheetStates
from app.bot.keyboards import (
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_timesheet_method_keyboard,
    get_objects_keyboard,
    get_add_worker_keyboard,
    get_period_keyboard,
    get_skip_comment_keyboard,
    get_webapp_keyboard
)
from app.bot.utils import APIClient
from app.core.database import AsyncSessionLocal
from app.core.database import AsyncSessionLocal
from app.models import SavedWorker, User
from app.bot.config import config

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
    """Начало подачи табеля - через Web App"""
    # Сохраняем токен если есть
    data = await state.get_data()
    token = data.get("token")
    
    # Получаем объекты
    client = APIClient(token)
    try:
        # Если токена нет, пробуем авторизоваться
        if not token:
            print(f"DEBUG: Token missing, attempting auto-login for {message.from_user.id}")
            new_token = await client.login_telegram(message.from_user.id)
            if new_token:
                token = new_token
                await state.update_data(token=token)
                client.token = token # Update client token
                print("DEBUG: Auto-login successful")
            else:
                print("DEBUG: Auto-login failed")
                await message.answer("⚠️ Вы не авторизованы. Используйте /start.")
                return 

        print(f"DEBUG: Fetching objects with token: {token[:10]}...")
        # NOTE: get_objects uses self.client.get but does NOT take `token` param in method (it uses self.token)
        # However, earlier code showed usage `objects = await client.get_objects()` which is correct
        objects = await client.get_objects()
        print(f"DEBUG: Fetched {len(objects)} objects")
    except Exception as e:
        print(f"ERROR getting objects: {e}")
        # await message.answer(f"⚠️ Ошибка получения объектов: {str(e)}")
        objects = []
    finally:
        await client.close()

    # Формируем список имен объектов для URL
    # Передаем: "Объект 1,Объект 2"
    obj_names = [o.get("name", "Unknown") for o in objects]
    obj_names_str = ",".join(obj_names)
    
    # Кодируем для URL
    params = {"objects": obj_names_str}
    query_string = urllib.parse.urlencode(params) 
    
    # Итоговый URL
    full_url = f"{config.web_app_url}?v=3.5&{query_string}"
    
    # Использование ReplyKeyboard для поддержки tg.sendData
    from app.bot.keyboards import get_webapp_reply_keyboard
    
    await message.answer(
        "📊 <b>Подача табеля РТБ (V3 Wizard)</b>\n\n"
        "👇 <b>Нажмите кнопку ВНИЗУ ЭКРАНА</b> (на клавиатуре), чтобы открыть форму:",
        parse_mode="HTML",
        reply_markup=get_webapp_reply_keyboard(full_url)
    )
    # Состояние можно не ставить, т.к. ответ придет в любом состоянии или без него



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


    # Состояние можно не ставить, т.к. ответ придет в любом состоянии или без него


@router.message(F.web_app_data)
async def process_webapp_data(message: Message, state: FSMContext):
    """Обработка данных из Web App"""
    try:
        data = json.loads(message.web_app_data.data)
        print(f"DEBUG: Received parsed web_app_data: {data}")
        
        # Проверка типа данных
        data_type = data.get('type')
        if data_type not in ['rtb_submission', 'rtb_submission_v2', 'rtb_batch_submission']:
            return
            
        object_name = data.get('object')
        
        # Начинаем работу с БД
        async with AsyncSessionLocal() as session:
            # 1. Получаем пользователя (прораба) по Telegram ID
            stmt = select(User).where(User.telegram_chat_id == message.chat.id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                await message.answer("❌ Ошибка: пользователь не найден. Пройдите авторизацию /login.")
                return

            # 2. Ищем или создаем Бригаду пользователя
            from app.models import Brigade, BrigadeMember, CostObject, TimeSheet, TimeSheetItem, SavedWorker
            
            # Получаем активную бригаду
            stmt = select(Brigade).where(Brigade.foreman_id == user.id, Brigade.is_active == True)
            result = await session.execute(stmt)
            brigade = result.scalars().first()
            
            if not brigade:
                brigade = Brigade(foreman_id=user.id, name=f"Бригада {user.username}")
                session.add(brigade)
                await session.flush()
                
            # 3. Находим Объект
            stmt = select(CostObject).where(CostObject.name == object_name)
            result = await session.execute(stmt)
            cost_object = result.scalars().first()
            
            if not cost_object:
                stmt = select(CostObject).where(CostObject.code == object_name)
                result = await session.execute(stmt)
                cost_object = result.scalars().first()
                
            if not cost_object:
                await message.answer(f"❌ Объект '{object_name}' не найден в системе.")
                return

            # Helper function
            total_items_created = 0
            
            async def process_entry(date_obj, w_name, w_hours):
                nonlocal total_items_created
                # Find/Create Member
                stmt = select(BrigadeMember).where(BrigadeMember.brigade_id == brigade.id, BrigadeMember.full_name == w_name)
                res = await session.execute(stmt)
                member = res.scalars().first()
                
                if not member:
                    member = BrigadeMember(brigade_id=brigade.id, full_name=w_name)
                    session.add(member)
                    await session.flush()
            
                # Update Saved Worker
                stmt = select(SavedWorker).where(SavedWorker.foreman_id == user.id, SavedWorker.name == w_name)
                res = await session.execute(stmt)
                if not res.scalars().first():
                    session.add(SavedWorker(foreman_id=user.id, name=w_name))

                # Create TimeSheet (Daily)
                ts = TimeSheet(
                    brigade_id=brigade.id,
                    period_start=date_obj,
                    period_end=date_obj,
                    status="DRAFT", 
                    notes="WebApp V2"
                )
                session.add(ts)
                await session.flush()
                
                item = TimeSheetItem(
                    time_sheet_id=ts.id,
                    member_id=member.id,
                    date=date_obj,
                    cost_object_id=cost_object.id,
                    hours=float(w_hours)
                )
                session.add(item)
                total_items_created += 1

            # --- V1 Parsing ---
            if data_type == 'rtb_submission':
                date_str = data.get('date')
                worker_names = data.get('workers')
                hours = float(data.get('hours', 0))
                work_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                for w_name in worker_names:
                    await process_entry(work_date, w_name, hours)

            # --- V2 Parsing (Range + Individual) ---
            elif data_type == 'rtb_submission_v2':
                start_str = data.get('start_date')
                end_str = data.get('end_date')
                workers_data = data.get('workers')
                
                s_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                e_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                
                from datetime import timedelta
                delta = (e_date - s_date).days
                
                for i in range(delta + 1):
                    current = s_date + timedelta(days=i)
                    for w in workers_data:
                        try:
                            w_hours = float(w.get('hours', 8))
                        except:
                            w_hours = 8.0
                        await process_entry(current, w['name'], w_hours)

            # --- V3 Parsing (Batch / Wizard) ---
            elif data_type == 'rtb_batch_submission':
                entries = data.get('entries', []) # List of {date, workers}
                print(f"DEBUG: Processing batch with {len(entries)} days")
                
                for entry in entries:
                    date_str = entry.get('date')
                    day_workers = entry.get('workers', [])
                    
                    work_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    for w in day_workers:
                        try:
                            w_hours = float(w.get('hours', 8))
                        except:
                            w_hours = 8.0
                        await process_entry(work_date, w['name'], w_hours)

            await session.commit()
            
            # Determine period for message
            period_str = ""
            if data_type == 'rtb_batch_submission':
                dates = [e['date'] for e in entries]
                if dates:
                    period_str = f"{min(dates)} - {max(dates)}"
            else:
                period_str = f"{data.get('start_date', '')} - {data.get('end_date', '')}"

            await message.answer(
                f"✅ <b>Отчет принят!</b>\n"
                f"📅 Период: {period_str}\n"
                f"🏗 Объект: {object_name}\n"
                f"📝 Записей создано: {total_items_created}",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        await message.answer(f"❌ Произошла ошибка при сохранении: {str(e)}")


# =============================================================================
# СПОСОБ 1: Скачать шаблон (Deprecated but kept)
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
