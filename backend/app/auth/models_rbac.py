"""
Модели RBAC (Role-Based Access Control)
Динамическая система ролей и прав доступа.

Таблицы:
  - Role:           Кастомные роли (напр. "Старший прораб", "Снабженец")
  - Permission:     Гранулярные права (напр. "material_requests.create")  
  - RolePermission: Связь M:N — какие права входят в роль
  - UserRoleLink:   Связь M:N — какие роли назначены пользователю

Миграция:
  Существующее поле `User.roles: JSON` (массив строк) остаётся как legacy.
  Скрипт /scripts/migrate_rbac.py перенесёт данные в новые таблицы.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Role(Base):
    """
    Роль пользователя (динамическая).
    Системные роли (ADMIN, MANAGER, FOREMAN, ...) создаются миграцией.
    Новые роли можно создавать через UI.
    """
    __tablename__ = "rbac_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)       # "ADMIN", "FOREMAN", "Старший прораб"
    display_name = Column(String(200), nullable=False)                         # "Администратор", "Бригадир"
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)                 # True = нельзя удалить/переименовать
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    users = relationship(
        "UserRoleLink", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """
    Гранулярное право доступа.
    Формат: ресурс.действие (напр. "material_requests.create", "objects.view")
    """
    __tablename__ = "rbac_permissions"

    id = Column(Integer, primary_key=True, index=True)
    codename = Column(String(150), unique=True, nullable=False, index=True)   # "material_requests.create"
    display_name = Column(String(200), nullable=False)                         # "Создание заявок на материалы"
    resource = Column(String(100), nullable=False, index=True)                 # "material_requests"
    action = Column(String(50), nullable=False)                                # "create"
    description = Column(Text, nullable=True)

    # Связи
    roles = relationship("RolePermission", back_populates="permission")

    def __repr__(self):
        return f"<Permission {self.codename}>"


class RolePermission(Base):
    """Связь M:N: Роль ↔ Право"""
    __tablename__ = "rbac_role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("rbac_permissions.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")


class UserRoleLink(Base):
    """
    Связь M:N: Пользователь ↔ Роль.
    Один пользователь может иметь несколько ролей.
    """
    __tablename__ = "rbac_user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    role = relationship("Role", back_populates="users")
