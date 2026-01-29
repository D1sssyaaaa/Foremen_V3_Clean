"""Сервис для предпросмотра Excel загрузок табелей"""
import uuid
import tempfile
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Brigade, BrigadeMember, CostObject
from app.time_sheets.excel_parser import TimeSheetExcelParser, TimeSheetExcelParseError


class ExcelPreviewService:
    """Сервис для работы с предпросмотром Excel загрузок"""
    
    # Временное хранилище preview данных (в памяти)
    # В продакшене лучше использовать Redis
    _preview_storage: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_preview(
        self,
        file_content: bytes,
        brigade_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Создание предпросмотра из Excel файла
        
        Args:
            file_content: содержимое файла
            brigade_id: ID бригады
            user_id: ID пользователя
            
        Returns:
            dict с данными preview и уникальным ID
            
        Raises:
            ValueError: если файл не валиден
        """
        # Сохранение во временный файл
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Парсинг Excel
            try:
                parser = TimeSheetExcelParser(temp_file_path)
                parsed_data = parser.parse()
            except TimeSheetExcelParseError as e:
                raise ValueError(f"Ошибка парсинга Excel: {str(e)}")
            
            # Проверка бригады
            brigade = await self.db.get(Brigade, brigade_id)
            if not brigade:
                raise ValueError(f"Бригада {brigade_id} не найдена")
            
            # Валидация и обогащение данных
            validated_items = await self._validate_and_enrich(
                parsed_data['items'],
                brigade_id
            )
            
            # Подсчёт статистики
            stats = self._calculate_stats(validated_items)
            
            # Генерация уникального ID для preview
            preview_id = str(uuid.uuid4())
            
            # Сохранение в хранилище
            preview_data = {
                'preview_id': preview_id,
                'user_id': user_id,
                'brigade_id': brigade_id,
                'brigade_name': brigade.name,
                'period_start': parsed_data['period_start'].isoformat(),
                'period_end': parsed_data['period_end'].isoformat(),
                'items': validated_items,
                'stats': stats,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().timestamp() + 3600)  # Истекает через 1 час
            }
            
            self._preview_storage[preview_id] = preview_data
            
            return preview_data
        
        finally:
            # Удаление временного файла
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    async def _validate_and_enrich(
        self,
        items: List[Dict],
        brigade_id: int
    ) -> List[Dict]:
        """
        Валидация и обогащение данных из Excel
        
        Args:
            items: строки из Excel
            brigade_id: ID бригады
            
        Returns:
            список обогащённых и провалидированных строк
        """
        # Получение членов бригады
        brigade = await self.db.get(Brigade, brigade_id, options=[])
        stmt = select(BrigadeMember).where(BrigadeMember.brigade_id == brigade_id)
        result = await self.db.execute(stmt)
        members = result.scalars().all()
        member_map = {m.full_name.strip().lower(): m for m in members}
        
        # Получение всех объектов
        stmt = select(CostObject).where(CostObject.is_active == True)
        result = await self.db.execute(stmt)
        objects = result.scalars().all()
        object_map = {o.name.strip().lower(): o for o in objects}
        
        validated_items = []
        errors = []
        warnings = []
        
        for idx, item in enumerate(items, start=1):
            row_data = {
                'row_number': idx,
                'member_name': item['member_name'],
                'date': item['date'].isoformat() if isinstance(item['date'], date) else item['date'],
                'cost_object_name': item['cost_object_name'],
                'hours': float(item['hours']),
                'valid': True,
                'errors': [],
                'warnings': [],
                'member_id': None,
                'cost_object_id': None
            }
            
            # Валидация сотрудника
            member_key = item['member_name'].strip().lower()
            if member_key in member_map:
                member = member_map[member_key]
                row_data['member_id'] = member.id
                row_data['member_verified'] = True
            else:
                row_data['valid'] = False
                row_data['errors'].append(f"Сотрудник '{item['member_name']}' не найден в бригаде")
            
            # Валидация объекта
            object_key = item['cost_object_name'].strip().lower()
            if object_key in object_map:
                obj = object_map[object_key]
                row_data['cost_object_id'] = obj.id
                row_data['cost_object_verified'] = True
            else:
                row_data['valid'] = False
                row_data['errors'].append(f"Объект '{item['cost_object_name']}' не найден")
            
            # Валидация часов
            if item['hours'] <= 0:
                row_data['valid'] = False
                row_data['errors'].append(f"Некорректное количество часов: {item['hours']}")
            elif item['hours'] > 12:
                row_data['warnings'].append(f"Переработка: {item['hours']} часов (>12)")
            elif item['hours'] > 24:
                row_data['valid'] = False
                row_data['errors'].append(f"Невозможное количество часов: {item['hours']}")
            
            # Валидация даты
            try:
                if isinstance(item['date'], str):
                    datetime.fromisoformat(item['date'])
            except ValueError:
                row_data['valid'] = False
                row_data['errors'].append(f"Некорректная дата: {item['date']}")
            
            validated_items.append(row_data)
        
        return validated_items
    
    def _calculate_stats(self, items: List[Dict]) -> Dict:
        """Подсчёт статистики по данным"""
        total_rows = len(items)
        valid_rows = sum(1 for item in items if item['valid'])
        invalid_rows = total_rows - valid_rows
        total_hours = sum(item['hours'] for item in items if item['valid'])
        overtime_cases = sum(1 for item in items if item['hours'] > 12)
        
        # Уникальные сотрудники и объекты
        unique_members = len(set(item['member_name'] for item in items))
        unique_objects = len(set(item['cost_object_name'] for item in items))
        
        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'total_hours': float(total_hours),
            'overtime_cases': overtime_cases,
            'unique_members': unique_members,
            'unique_objects': unique_objects,
            'has_errors': invalid_rows > 0,
            'has_warnings': overtime_cases > 0
        }
    
    def get_preview(self, preview_id: str, user_id: int) -> Optional[Dict]:
        """
        Получение preview по ID
        
        Args:
            preview_id: ID preview
            user_id: ID пользователя (для проверки прав)
            
        Returns:
            данные preview или None
        """
        preview_data = self._preview_storage.get(preview_id)
        
        if not preview_data:
            return None
        
        # Проверка истечения времени
        if datetime.now().timestamp() > preview_data['expires_at']:
            self.delete_preview(preview_id)
            return None
        
        # Проверка прав доступа
        if preview_data['user_id'] != user_id:
            return None
        
        return preview_data
    
    def delete_preview(self, preview_id: str) -> bool:
        """Удаление preview из хранилища"""
        if preview_id in self._preview_storage:
            del self._preview_storage[preview_id]
            return True
        return False
    
    def cleanup_expired(self):
        """Очистка истекших preview (вызывается периодически)"""
        now = datetime.now().timestamp()
        expired = [
            pid for pid, data in self._preview_storage.items()
            if data['expires_at'] < now
        ]
        for pid in expired:
            del self._preview_storage[pid]
        return len(expired)
