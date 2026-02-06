import io
import logging
import openpyxl
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models import CostObject, EstimateItem

logger = logging.getLogger(__name__)

class EstimateService:
    @staticmethod
    async def parse_and_save_excel(
        session: AsyncSession,
        object_id: int,
        file: UploadFile,
        commit: bool = True
    ):
        """
        Парсинг Excel сметы и сохранение позиций.
        """
        
        # 1. Проверка объекта
        obj = await session.get(CostObject, object_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Объект не найден")
            
        # 2. Удаление старых позиций
        await session.execute(delete(EstimateItem).where(EstimateItem.cost_object_id == object_id))
        
        # 3. Чтение файла
        try:
            logger.info(f"Начинаю чтение файла сметы: {file.filename}")
            content = await file.read()
            logger.info(f"Прочитано байт: {len(content)}")
            
            # Используем BytesIO для гарантии бинарного режима
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            ws = wb.active
        except Exception as e:
            logger.error(f"Ошибка загрузки Excel: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Ошибка чтения Excel: {str(e)}")
            
        items_to_create = []
        current_category = "Общее"
        total_estimate_sum = 0.0
        
        # Пропускаем заголовок (обычно 1 строка, но ищем начало данных)
        # Предполагаем, что данные начинаются, когда в колонке A есть число, 
        # или в колонке B есть текст (категория)
        
        start_row = 2 # Обычно 1-я строка шапка
        
        for row in ws.iter_rows(min_row=start_row, values_only=True):
            # row index is 0-based tuple: A=0, B=1, C=2, D=3, E=4, F=5
            col_a = row[0] # №
            col_b = row[1] # Наименование / Категория
            
            if not col_b: 
                continue # Пустая строка
                
            # Improved logic:
            # Check if it looks like an item: has Name (B) and at least Unit (C) or Qty (D) or Price (E)
            # Row index matches: A=0, B=1, C=2, D=3, E=4, F=5
            
            name = str(col_b).strip() if col_b else ""
            
            # Helper to safe float
            def safe_float(val):
                try:
                    if not val: return 0.0
                    return float(val)
                except:
                    return 0.0

            is_item = False
            
            # Strategy 1: Column A is a digit (classic)
            if col_a and str(col_a).strip().replace('.', '').isdigit():
                is_item = True
            
            # Strategy 2: Heuristic - if it has unit and price/qty, it's likely an item, even without Col A
            # Check cols C (unit), D (qty), E (price)
            val_c = row[2]
            val_d = row[3]
            val_e = row[4]
            
            if not is_item and name:
                 # If we have a unit (e.g. "шт", "м2") or generic numeric data in D/E
                 has_unit = val_c and len(str(val_c)) < 10 # Unit is usually short
                 has_qty = isinstance(val_d, (int, float)) or (isinstance(val_d, str) and val_d.strip().replace('.', '').isdigit())
                 
                 if has_unit or has_qty:
                     is_item = True

            if is_item:
                # It is an item
                try:
                    unit = str(val_c).strip() if val_c else "шт"
                    qty = safe_float(val_d)
                    price = safe_float(val_e)
                    total = safe_float(row[5])
                    
                    if total == 0 and qty > 0 and price > 0:
                        total = qty * price
                    
                    item = EstimateItem(
                        cost_object_id=object_id,
                        category=current_category,
                        name=name,
                        unit=unit,
                        quantity=qty,
                        price=price,
                        total_amount=total
                    )
                    items_to_create.append(item)
                    total_estimate_sum += total
                except Exception as e:
                    logger.warning(f"Ошибка парсинга строки {row}: {e}")
            else:
                # It might be a category
                # If it has a name but no valid item data, treat as category
                items_in_row = [row[3], row[4], row[5]] # qty, price, sum
                is_data_empty = all(not x for x in items_in_row)
                
                if name and len(name) > 2 and is_data_empty:
                     current_category = name
                     
        # 4. Сохранение
        if items_to_create:
            session.add_all(items_to_create)
            
            # Обновляем общую сумму материалов в объекте
            obj.material_amount = total_estimate_sum
            
            if commit:
                await session.commit()
            else:
                await session.flush() # Ensure ID is available if needed, but don't commit transaction
            return {
                "status": "success", 
                "items_count": len(items_to_create), 
                "total_amount": total_estimate_sum
            }
        else:
            return {"status": "empty", "message": "Не найдено позиций в файле"}

    @staticmethod
    async def get_estimate_items(session: AsyncSession, object_id: int):
        """
        Получение списка позиций сметы для объекта
        """
        # Импорт внутри метода во избежание циклического импорта, если нужно
        from app.models import EstimateItem
        from sqlalchemy import select
        
        result = await session.execute(
            select(EstimateItem)
            .where(EstimateItem.cost_object_id == object_id)
            .order_by(EstimateItem.id) 
        )
        return result.scalars().all()
