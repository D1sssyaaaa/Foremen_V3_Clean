"""FSM состояния для создания заявок на материалы"""
from aiogram.fsm.state import State, StatesGroup


class MaterialRequestStates(StatesGroup):
    """Состояния создания заявки на материалы"""
    # Шаг 1: Выбор объекта
    select_object = State()
    
    # Шаг 2: Выбор типа материала (regular/inert)
    select_material_type = State()
    
    # Шаг 3: Указание времени доставки (только для inert)
    input_delivery_time = State()
    
    # Шаг 4: Указание срочности
    select_urgency = State()
    
    # Шаг 5: Выбор даты поставки (кнопки или ввод)
    input_required_date = State()
    input_custom_date = State()
    
    # Шаг 6: Добавление позиций материалов (одной строкой: "Песок 10 т")
    input_material_item = State()
    add_material_item = State()
    
    # Шаг 7: Комментарий (опционально)
    input_comment = State()
    
    # Шаг 8: Подтверждение
    confirm = State()


class EquipmentOrderStates(StatesGroup):
    """Состояния создания заявки на технику"""
    select_object = State()
    select_equipment_type = State()
    select_start_date = State()  # Выбор даты через кнопки
    input_start_date = State()    # Ручной ввод даты
    input_duration = State()
    input_description = State()
    confirm = State()
    
    # Отмена заявки
    cancel_reason = State()  # Ввод причины отмены


class TimeSheetStates(StatesGroup):
    """Состояния подачи табеля РТБ"""
    # Выбор способа подачи (шаблон / ручной ввод / Excel)
    select_method = State()
    
    # === Загрузка Excel ===
    upload_file = State()
    
    # === Ручной ввод: создание бригады ===
    select_object = State()  # Выбор объекта
    input_period_start = State()  # Начало периода
    input_period_end = State()  # Конец периода
    
    # === Ручной ввод: добавление работников ===
    input_worker_name = State()  # ФИО работника
    input_worker_birth_date = State()  # Дата рождения
    input_worker_phone = State()  # Телефон
    add_more_workers = State()  # Добавить еще работника?
    
    # === Ручной ввод: часы работы ===
    input_worker_hours = State()  # Часы для работника
    next_worker_hours = State()  # Переход к следующему работнику
    
    # === Общее ===
    input_comment = State()
    confirm = State()


class RegistrationStates(StatesGroup):
    """Состояния регистрации нового пользователя (заявка)"""
    input_full_name = State()
    input_birth_date = State()
    input_phone = State()
    confirm = State()

class DeliveryStates(StatesGroup):
    """Состояния создания заявки на доставку материалов"""
    # Шаг 1: Выбор объекта
    select_object = State()
    
    # Шаг 2: Ввод суммы доставки
    input_amount = State()
    
    # Шаг 3: Ввод даты доставки
    input_delivery_date = State()
    
    # Шаг 4: Комментарий (опционально)
    input_comment = State()
    
    # Шаг 5: Подтверждение
    confirm = State()