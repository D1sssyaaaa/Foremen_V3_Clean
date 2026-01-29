"""Простое создание тестовых данных"""
import sqlite3
import json
import hashlib
from datetime import date

def hash_pw(pw):
    """SHA256 хеш для совместимости"""
    return hashlib.sha256(pw.encode()).hexdigest()

conn = sqlite3.connect('construction_costs.db')
cur = conn.cursor()

print("\n=== Создание тестовых данных ===\n")

# Пользователи
users = [
    ('admin', '+79001111111', 'admin@example.com', hash_pw('admin123'), json.dumps(['ADMIN', 'MANAGER']), None, 1, 'Администратор Системы'),
    ('accountant', '+79002222222', 'accountant@example.com', hash_pw('acc123'), json.dumps(['ACCOUNTANT']), None, 1, 'Иванова Мария Петровна'),
    ('hr_manager', '+79003333333', 'hr@example.com', hash_pw('hr123'), json.dumps(['HR_MANAGER']), None, 1, 'Сидоров Алексей Иванович'),
    ('foreman1', '+79004444444', 'foreman1@example.com', hash_pw('for123'), json.dumps(['FOREMAN']), '123456789', 1, 'Петров Иван Сергеевич'),
    ('foreman2', '+79005555555', None, hash_pw('for123'), json.dumps(['FOREMAN']), None, 1, 'Смирнов Петр Дмитриевич'),
    ('materials_manager', '+79006666666', None, hash_pw('mat123'), json.dumps(['MATERIALS_MANAGER']), None, 1, 'Козлова Елена Викторовна'),
    ('equipment_manager', '+79007777777', None, hash_pw('eq123'), json.dumps(['EQUIPMENT_MANAGER']), None, 1, 'Морозов Сергей Александрович'),
]

cur.executemany(
    'INSERT INTO users (username, phone, email, hashed_password, roles, telegram_chat_id, is_active, full_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    users
)
print(f"+ Создано {len(users)} пользователей")

# Объекты
objects = [
    ("Жилой комплекс 'Светлый'", 'ZHK-001', 'Д-2025-001', 150000000.0, None, None, 1, 'Строительство 3-х секционного жилого дома'),
    ("Торговый центр 'Галерея'", 'TC-002', 'Д-2025-002', 85000000.0, None, None, 1, 'Реконструкция торгового центра'),
    ("Офисное здание 'Бизнес-Парк'", 'OF-003', 'Д-2025-003', 120000000.0, None, None, 1, 'Строительство офисного комплекса класса А'),
    ("Школа №45", 'SH-004', 'Д-2025-004', 95000000.0, None, None, 1, 'Строительство общеобразовательной школы'),
    ("Спортивный комплекс", 'SK-005', 'Д-2025-005', 65000000.0, None, None, 1, 'Строительство универсального спортзала'),
]

cur.executemany(
    'INSERT INTO cost_objects (name, code, contract_number, contract_amount, start_date, end_date, is_active, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    objects
)
print(f"+ Создано {len(objects)} объектов")

# Бригады
brigades = [
    (4, 'Бригада №1 (Общестрой)', 1),  # foreman1
    (5, 'Бригада №2 (Отделка)', 1),     # foreman2
]

cur.executemany(
    'INSERT INTO brigades (foreman_id, name, is_active) VALUES (?, ?, ?)',
    brigades
)
print(f"+ Создано {len(brigades)} бригад")

# Рабочие
members = [
    # Бригада 1
    (1, 'Кузнецов Андрей', 'Прораб', 500.0, 1),
    (1, 'Волков Дмитрий', 'Каменщик', 400.0, 1),
    (1, 'Зайцев Михаил', 'Каменщик', 400.0, 1),
    (1, 'Соколов Николай', 'Подсобник', 300.0, 1),
    (1, 'Лебедев Виктор', 'Подсобник', 300.0, 1),
    # Бригада 2
    (2, 'Новиков Александр', 'Мастер', 480.0, 1),
    (2, 'Федоров Игорь', 'Маляр', 380.0, 1),
    (2, 'Егоров Василий', 'Штукатур', 390.0, 1),
    (2, 'Макаров Олег', 'Плиточник', 420.0, 1),
]

cur.executemany(
    'INSERT INTO brigade_members (brigade_id, full_name, position, hourly_rate, is_active) VALUES (?, ?, ?, ?, ?)',
    members
)
print(f"+ Создано {len(members)} рабочих")

# Заявки
mat_req = [(1, 4, 'НОВАЯ', 'срочная', 'Для секции №1, 3 этаж', 'regular')]
cur.executemany(
    'INSERT INTO material_requests (cost_object_id, foreman_id, status, urgency, notes, material_type) VALUES (?, ?, ?, ?, ?, ?)',
    mat_req
)

eq_order = [(1, 4, 'Автокран 25т', 1, 'Для монтажа плит перекрытия', 'НОВАЯ', str(date.today()))]
cur.executemany(
    'INSERT INTO equipment_orders (cost_object_id, foreman_id, equipment_type, quantity, description, status, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
    eq_order
)
print(f"+ Создано 2 заявки")

conn.commit()
conn.close()

print("\n" + "="*60)
print("[OK] ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
print("="*60)
print("\n Итого:")
print(f"   • Пользователей: {len(users)}")
print(f"   • Объектов: {len(objects)}")
print(f"   • Бригад: {len(brigades)}")
print(f"   • Рабочих: {len(members)}")
print("   • Заявок: 2")
print("\n Учетные данные:")
print("   admin / admin123")
print("   accountant / acc123")
print("   foreman1 / for123")
print("   materials_manager / mat123")
print()
