"""
Скрипт миграции на динамическую систему ролей (RBAC).

Что делает:
  1. Создаёт новые таблицы (rbac_roles, rbac_permissions, rbac_role_permissions, rbac_user_roles, product_aliases)
  2. Добавляет колонку file_hash в material_costs (если отсутствует)
  3. Создаёт системные роли из текущего UserRole enum
  4. Создаёт базовые права (permissions)
  5. Назначает права системным ролям
  6. Переносит текущие роли пользователей (из JSON поля `roles`) в таблицу rbac_user_roles

Безопасность:
  - Скрипт идемпотентный — можно запускать повторно
  - Существующие данные НЕ удаляются
  - Поле User.roles (JSON) остаётся как legacy fallback
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.models_base import UserRole
from app.models import User
from app.auth.models_rbac import Role, Permission, RolePermission, UserRoleLink
from app.materials.models_mapping import ProductAlias

# ============================================================
# Конфигурация: системные роли и их display_name
# ============================================================
SYSTEM_ROLES = {
    "ADMIN":                {"display_name": "Администратор",           "description": "Полный доступ ко всем функциям системы"},
    "MANAGER":              {"display_name": "Руководитель",            "description": "Управление объектами, просмотр аналитики, согласование"},
    "FOREMAN":              {"display_name": "Бригадир",                "description": "Управление бригадой, создание заявок, табели"},
    "ACCOUNTANT":           {"display_name": "Бухгалтер",               "description": "Просмотр финансовых данных, загрузка УПД"},
    "HR_MANAGER":           {"display_name": "Менеджер по персоналу",   "description": "Управление сотрудниками и доступами"},
    "EQUIPMENT_MANAGER":    {"display_name": "Менеджер по технике",     "description": "Управление заявками на технику"},
    "MATERIALS_MANAGER":    {"display_name": "Менеджер по снабжению",   "description": "Управление заявками на материалы и УПД"},
    "PROCUREMENT_MANAGER":  {"display_name": "Менеджер по закупкам",    "description": "Закупки, работа с поставщиками"},
}

# ============================================================
# Конфигурация: базовые permissions
# ============================================================
BASE_PERMISSIONS = [
    # Объекты
    ("objects.view",             "Просмотр объектов",              "objects",            "view"),
    ("objects.create",           "Создание объектов",              "objects",            "create"),
    ("objects.edit",             "Редактирование объектов",        "objects",            "edit"),
    ("objects.delete",           "Удаление объектов",              "objects",            "delete"),
    ("objects.assign_users",     "Назначение пользователей",       "objects",            "assign_users"),
    # Заявки на материалы
    ("material_requests.view",   "Просмотр заявок на материалы",   "material_requests",  "view"),
    ("material_requests.create", "Создание заявок на материалы",   "material_requests",  "create"),
    ("material_requests.edit",   "Редактирование заявок",          "material_requests",  "edit"),
    ("material_requests.approve","Согласование заявок",            "material_requests",  "approve"),
    ("material_requests.status", "Изменение статуса заявок",       "material_requests",  "status"),
    # УПД
    ("upd.view",                 "Просмотр УПД",                   "upd",                "view"),
    ("upd.upload",               "Загрузка УПД",                   "upd",                "upload"),
    ("upd.distribute",           "Распределение УПД",              "upd",                "distribute"),
    # Техника
    ("equipment.view",           "Просмотр заявок на технику",     "equipment",          "view"),
    ("equipment.create",         "Создание заявок на технику",     "equipment",          "create"),
    ("equipment.approve",        "Согласование заявок на технику", "equipment",          "approve"),
    ("equipment.costs",          "Управление стоимостью техники",  "equipment",          "costs"),
    # Пользователи
    ("users.view",               "Просмотр пользователей",         "users",              "view"),
    ("users.edit",               "Редактирование пользователей",   "users",              "edit"),
    ("users.manage_roles",       "Управление ролями",              "users",              "manage_roles"),
    # Аналитика
    ("analytics.view",           "Просмотр аналитики",             "analytics",          "view"),
    # Сметы
    ("estimates.view",           "Просмотр смет",                  "estimates",          "view"),
    ("estimates.edit",           "Редактирование смет",            "estimates",          "edit"),
]

# ============================================================
# Конфигурация: какие права получает каждая роль
# ============================================================
ROLE_PERMISSIONS_MAP = {
    "ADMIN": "*",  # все права
    "MANAGER": [
        "objects.*", "material_requests.*", "upd.*",
        "equipment.*", "users.view", "analytics.view",
        "estimates.*",
    ],
    "FOREMAN": [
        "objects.view", "material_requests.view", "material_requests.create",
        "equipment.view", "equipment.create", "estimates.view",
    ],
    "ACCOUNTANT": [
        "objects.view", "upd.view", "upd.upload", "upd.distribute",
        "analytics.view", "material_requests.view",
    ],
    "HR_MANAGER": [
        "users.view", "users.edit", "objects.view",
    ],
    "EQUIPMENT_MANAGER": [
        "equipment.*", "objects.view", "analytics.view",
    ],
    "MATERIALS_MANAGER": [
        "material_requests.*", "upd.*", "objects.view",
        "estimates.view", "analytics.view",
    ],
    "PROCUREMENT_MANAGER": [
        "material_requests.view", "material_requests.status",
        "upd.view", "upd.upload", "objects.view",
    ],
}


def match_permission(codename: str, patterns: list) -> bool:
    """Проверяет, подходит ли permission под паттерн (поддержка wildcard *)."""
    for pattern in patterns:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            resource = pattern[:-2]
            if codename.startswith(resource + "."):
                return True
        elif pattern == codename:
            return True
    return False


async def migrate():
    """Основная функция миграции."""
    print("🚀 Запуск миграции RBAC...\n")

    # === Шаг 1: Создать новые таблицы ===
    print("📦 Шаг 1: Создание новых таблиц...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✅ Таблицы созданы (или уже существуют)\n")

    # === Шаг 2: Добавить file_hash, если нет ===
    print("📦 Шаг 2: Проверка колонки file_hash в material_costs...")
    async with engine.begin() as conn:
        # Проверяем наличие колонки
        def check_column(sync_conn):
            insp = inspect(sync_conn)
            columns = [c["name"] for c in insp.get_columns("material_costs")]
            return "file_hash" in columns
        
        has_column = await conn.run_sync(check_column)
        
        if not has_column:
            await conn.execute(text(
                "ALTER TABLE material_costs ADD COLUMN file_hash VARCHAR(64)"
            ))
            print("   ✅ Колонка file_hash добавлена\n")
        else:
            print("   ℹ️  Колонка file_hash уже существует\n")

    async with AsyncSessionLocal() as db:
        # === Шаг 3: Создать системные роли ===
        print("👤 Шаг 3: Создание системных ролей...")
        role_objects = {}
        for role_name, meta in SYSTEM_ROLES.items():
            existing = await db.execute(
                text("SELECT id FROM rbac_roles WHERE name = :name"),
                {"name": role_name}
            )
            row = existing.fetchone()
            if row:
                role_objects[role_name] = row[0]
                print(f"   ℹ️  {role_name} ({meta['display_name']}) — уже есть")
            else:
                role = Role(
                    name=role_name,
                    display_name=meta["display_name"],
                    description=meta["description"],
                    is_system=True,
                )
                db.add(role)
                await db.flush()
                role_objects[role_name] = role.id
                print(f"   ✅ {role_name} ({meta['display_name']}) — создана")
        
        await db.commit()
        print()

        # === Шаг 4: Создать базовые permissions ===
        print("🔑 Шаг 4: Создание прав доступа (permissions)...")
        perm_objects = {}
        for codename, display, resource, action in BASE_PERMISSIONS:
            existing = await db.execute(
                text("SELECT id FROM rbac_permissions WHERE codename = :codename"),
                {"codename": codename}
            )
            row = existing.fetchone()
            if row:
                perm_objects[codename] = row[0]
            else:
                perm = Permission(
                    codename=codename,
                    display_name=display,
                    resource=resource,
                    action=action,
                )
                db.add(perm)
                await db.flush()
                perm_objects[codename] = perm.id
        
        await db.commit()
        print(f"   ✅ {len(perm_objects)} прав загружено\n")

        # === Шаг 5: Назначить права ролям ===
        print("🔗 Шаг 5: Назначение прав ролям...")
        for role_name, patterns in ROLE_PERMISSIONS_MAP.items():
            role_id = role_objects.get(role_name)
            if not role_id:
                continue
            
            count = 0
            for codename, perm_id in perm_objects.items():
                if match_permission(codename, [patterns] if isinstance(patterns, str) else patterns):
                    existing = await db.execute(
                        text("SELECT id FROM rbac_role_permissions WHERE role_id = :rid AND permission_id = :pid"),
                        {"rid": role_id, "pid": perm_id}
                    )
                    if not existing.fetchone():
                        db.add(RolePermission(role_id=role_id, permission_id=perm_id))
                        count += 1
            
            await db.commit()
            total_perms = sum(
                1 for c in perm_objects
                if match_permission(c, [patterns] if isinstance(patterns, str) else patterns)
            )
            print(f"   ✅ {role_name}: {total_perms} прав (новых: {count})")
        
        print()

        # === Шаг 6: Перенести роли пользователей ===
        print("👥 Шаг 6: Миграция ролей пользователей...")
        result = await db.execute(text("SELECT id, username, roles FROM users"))
        users = result.fetchall()
        
        migrated = 0
        skipped = 0
        for user_row in users:
            user_id = user_row[0]
            username = user_row[1]
            user_roles_json = user_row[2]
            
            # Парсим JSON роли
            if isinstance(user_roles_json, str):
                import json
                try:
                    user_roles_list = json.loads(user_roles_json)
                except:
                    user_roles_list = []
            elif isinstance(user_roles_json, list):
                user_roles_list = user_roles_json
            else:
                user_roles_list = []
            
            if not user_roles_list:
                skipped += 1
                continue
            
            for role_name in user_roles_list:
                role_id = role_objects.get(role_name)
                if not role_id:
                    print(f"   ⚠️  Роль '{role_name}' у пользователя {username} — НЕ НАЙДЕНА в системных ролях, пропуск")
                    continue
                
                # Проверяем, нет ли уже связи
                existing = await db.execute(
                    text("SELECT id FROM rbac_user_roles WHERE user_id = :uid AND role_id = :rid"),
                    {"uid": user_id, "rid": role_id}
                )
                if not existing.fetchone():
                    db.add(UserRoleLink(user_id=user_id, role_id=role_id))
                    migrated += 1
            
            await db.commit()
        
        print(f"   ✅ Перенесено связей: {migrated}")
        print(f"   ℹ️  Пользователей без ролей: {skipped}")

    print("\n" + "=" * 50)
    print("✨ Миграция RBAC завершена успешно!")
    print("=" * 50)
    print("\nСводка:")
    print(f"  • Системных ролей: {len(SYSTEM_ROLES)}")
    print(f"  • Прав доступа: {len(BASE_PERMISSIONS)}")
    print(f"  • Пользователей обработано: {len(users)}")
    print(f"  • Связей создано: {migrated}")
    print("\n⚠️  Поле User.roles (JSON) НЕ удалено — оставлено как fallback.")
    print("    После тестирования можно убрать его из модели.\n")


if __name__ == "__main__":
    asyncio.run(migrate())
