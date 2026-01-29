"""Бизнес-логика модуля UPD"""
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    MaterialCost, MaterialCostItem, UPDDistribution, UPDDistributionHistory,
    CostEntry, MaterialRequest, CostObject, UPDStatus
)
from app.upd.upd_parser import UPDParser, UPDDocument, ParsingIssue
from app.upd.schemas import DistributionItemCreate


class UPDService:
    """Сервис для работы с УПД документами"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = UPDParser()
    
    async def upload_upd(
        self, 
        xml_content: bytes, 
        file_path: str,
        auto_check_duplicate: bool = True
    ) -> MaterialCost:
        """
        Загрузка и парсинг УПД из XML
        
        Args:
            xml_content: содержимое XML файла
            file_path: путь к сохраненному файлу в S3/MinIO
            auto_check_duplicate: автоматически проверять на дубликаты
            
        Returns:
            MaterialCost объект с распарсенными данными
        """
        # Парсинг XML
        try:
            upd_doc = self.parser.parse(xml_content)
        except ValueError as e:
            raise ValueError(f"Ошибка парсинга УПД: {str(e)}")
        
        # Проверка на дубликаты перед созданием
        duplicate = None
        if auto_check_duplicate:
            duplicate = await self.check_duplicate(
                document_number=upd_doc.document_number,
                document_date=upd_doc.document_date,
                supplier_inn=upd_doc.supplier_inn
            )
        
        # Создание записи в БД
        material_cost = MaterialCost(
            supplier_name=upd_doc.supplier_name,
            supplier_inn=upd_doc.supplier_inn,
            document_number=upd_doc.document_number,
            document_date=upd_doc.document_date,
            total_amount=upd_doc.total_amount,
            vat_amount=upd_doc.total_vat,
            xml_file_path=file_path,
            status=UPDStatus.DUPLICATE if duplicate else UPDStatus.NEW,
            duplicate_of_id=duplicate.id if duplicate else None,
            duplicate_checked_at=datetime.utcnow() if auto_check_duplicate else None,
            parsing_issues=self._serialize_issues(upd_doc.parsing_issues),
            generator=upd_doc.generator
        )
        
        self.db.add(material_cost)
        await self.db.flush()
        
        # Создание строк товаров/услуг
        for item in upd_doc.items:
            material_cost_item = MaterialCostItem(
                material_cost_id=material_cost.id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price,
                amount=item.amount,
                vat_rate=item.vat_rate,
                vat_amount=item.vat_amount
            )
            self.db.add(material_cost_item)
        
        await self.db.commit()
        # await self.db.refresh(material_cost)
        
        # Загружаем объект с items, чтобы избежать MissingGreenlet
        stmt = (
            select(MaterialCost)
            .options(selectinload(MaterialCost.items))
            .where(MaterialCost.id == material_cost.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def get_upd_by_id(self, upd_id: int) -> Optional[MaterialCost]:
        """Получение УПД по ID с загрузкой строк"""
        query = (
            select(MaterialCost)
            .options(selectinload(MaterialCost.items))
            .where(MaterialCost.id == upd_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_unprocessed_upds(self) -> List[MaterialCost]:
        """Получение необработанных УПД (статус NEW)"""
        query = (
            select(MaterialCost)
            .options(selectinload(MaterialCost.items))
            .where(MaterialCost.status == UPDStatus.NEW)
            .order_by(MaterialCost.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def distribute_upd(
        self,
        upd_id: int,
        distributions: List[DistributionItemCreate],
        user_id: Optional[int] = None
    ) -> MaterialCost:
        """
        Распределение УПД по заявкам/объектам
        
        Args:
            upd_id: ID УПД документа
            distributions: массив распределений
            user_id: ID пользователя (для истории)
            
        Returns:
            Обновленный MaterialCost
            
        Raises:
            ValueError: если УПД не найден или валидация не прошла
        """
        # Загрузка УПД
        upd = await self.get_upd_by_id(upd_id)
        if not upd:
            raise ValueError(f"УПД с ID {upd_id} не найден")
        
        if upd.status != UPDStatus.NEW:
            raise ValueError(f"УПД уже обработан (статус: {upd.status})")
        
        # Валидация распределений
        await self._validate_distributions(upd, distributions)
        
        # Создание записей распределения
        total_distributed = Decimal("0")
        cost_entries_count = 0
        
        for dist in distributions:
            # Получение строки УПД
            item = next(
                (i for i in upd.items if i.id == dist.material_cost_item_id),
                None
            )
            if not item:
                raise ValueError(f"Строка УПД {dist.material_cost_item_id} не найдена")
            
            # Определение объекта учета
            cost_object_id = dist.cost_object_id
            if dist.material_request_id:
                # Получение объекта из заявки
                request = await self.db.get(MaterialRequest, dist.material_request_id)
                if request:
                    cost_object_id = request.cost_object_id
            
            # Создание записи распределения
            distribution = UPDDistribution(
                material_cost_id=upd.id,
                material_cost_item_id=dist.material_cost_item_id,
                material_request_id=dist.material_request_id,
                cost_object_id=cost_object_id,
                distributed_quantity=dist.distributed_quantity,
                distributed_amount=dist.distributed_amount
            )
            self.db.add(distribution)
            
            # Создание записи затрат
            if cost_object_id:
                cost_entry = CostEntry(
                    type="material",
                    cost_object_id=cost_object_id,
                    date=upd.document_date,
                    amount=dist.distributed_amount,
                    description=f"УПД {upd.document_number}: {item.product_name}"
                )
                self.db.add(cost_entry)
                cost_entries_count += 1
            
            total_distributed += dist.distributed_amount
        
        # Обновление статуса УПД
        upd.status = UPDStatus.DISTRIBUTED
        upd.cost_object_id = distributions[0].cost_object_id if distributions else None
        
        # Логирование в историю
        if user_id:
            distribution_data = {
                "distributions": [
                    {
                        "material_cost_item_id": d.material_cost_item_id,
                        "material_request_id": d.material_request_id,
                        "cost_object_id": d.cost_object_id,
                        "distributed_quantity": float(d.distributed_quantity),
                        "distributed_amount": float(d.distributed_amount)
                    }
                    for d in distributions
                ],
                "total_amount": float(total_distributed)
            }
            
            await self.log_distribution_history(
                material_cost_id=upd_id,
                user_id=user_id,
                action="CREATE",
                old_distribution=None,
                new_distribution=distribution_data,
                description=f"Первичное распределение УПД №{upd.document_number}"
            )
        
        await self.db.commit()
        await self.db.refresh(upd)
        
        return upd
    
    async def _validate_distributions(
        self,
        upd: MaterialCost,
        distributions: List[DistributionItemCreate]
    ) -> None:
        """Валидация распределений УПД"""
        # Проверка, что все строки распределены корректно
        for dist in distributions:
            # Проверка существования строки
            item = next(
                (i for i in upd.items if i.id == dist.material_cost_item_id),
                None
            )
            if not item:
                raise ValueError(f"Строка УПД {dist.material_cost_item_id} не найдена")
            
            # Проверка количества
            if dist.distributed_quantity <= 0:
                raise ValueError("Распределенное количество должно быть > 0")
            
            if dist.distributed_quantity > (Decimal(str(item.quantity)) + Decimal("0.001")):
                raise ValueError(
                    f"Распределенное количество ({dist.distributed_quantity}) "
                    f"превышает доступное ({item.quantity})"
                )
            
            # Проверка суммы
            if dist.distributed_amount <= 0:
                raise ValueError("Распределенная сумма должна быть > 0")
            
            # Допускаем погрешность в 1 копейку
            max_amount = Decimal(str(item.amount)) + Decimal(str(item.vat_amount))
            if dist.distributed_amount > (max_amount + Decimal("0.01")):
                raise ValueError(
                    f"Распределенная сумма ({dist.distributed_amount}) "
                    f"превышает доступную ({max_amount})"
                )
            
            # Проверка наличия целевого объекта или заявки
            if not dist.material_request_id and not dist.cost_object_id:
                raise ValueError(
                    "Необходимо указать либо material_request_id, либо cost_object_id"
                )
            
            # Проверка существования заявки
            if dist.material_request_id:
                request = await self.db.get(MaterialRequest, dist.material_request_id)
                if not request:
                    raise ValueError(f"Заявка {dist.material_request_id} не найдена")
            
            # Проверка существования объекта
            if dist.cost_object_id:
                obj = await self.db.get(CostObject, dist.cost_object_id)
                if not obj:
                    raise ValueError(f"Объект {dist.cost_object_id} не найден")
    
    def _serialize_issues(self, issues: List[ParsingIssue]) -> str:
        """Сериализация проблем парсинга в JSON"""
        if not issues:
            return "[]"
        
        issues_data = [
            {
                "severity": issue.severity.value,
                "element": issue.element,
                "message": issue.message,
                "generator": issue.generator,
                "value": issue.value
            }
            for issue in issues
        ]
        return json.dumps(issues_data, ensure_ascii=False)
    
    def _deserialize_issues(self, issues_json: str) -> List[dict]:
        """Десериализация проблем парсинга из JSON"""
        if not issues_json:
            return []
        try:
            return json.loads(issues_json)
        except json.JSONDecodeError:
            return []
    
    async def check_duplicate(
        self, 
        document_number: str,
        document_date: datetime,
        supplier_inn: Optional[str] = None
    ) -> Optional[MaterialCost]:
        """
        Проверка на дубликат УПД
        
        Args:
            document_number: номер документа
            document_date: дата документа
            supplier_inn: ИНН поставщика (опционально)
            
        Returns:
            MaterialCost если дубликат найден, иначе None
        """
        query = select(MaterialCost).where(
            MaterialCost.document_number == document_number,
            MaterialCost.document_date == document_date,
            MaterialCost.status != UPDStatus.DUPLICATE  # Исключаем сами дубликаты
        )
        
        # Если есть ИНН, используем его для более точной проверки
        if supplier_inn:
            query = query.where(MaterialCost.supplier_inn == supplier_inn)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def mark_as_duplicate(
        self, 
        upd_id: int, 
        original_upd_id: int
    ) -> MaterialCost:
        """
        Пометить УПД как дубликат
        
        Args:
            upd_id: ID дубликата
            original_upd_id: ID оригинального УПД
            
        Returns:
            Обновленный MaterialCost
        """
        upd = await self.get_upd_by_id(upd_id)
        if not upd:
            raise ValueError(f"УПД {upd_id} не найден")
        
        # Проверяем существование оригинала
        original = await self.get_upd_by_id(original_upd_id)
        if not original:
            raise ValueError(f"Оригинальный УПД {original_upd_id} не найден")
        
        upd.status = UPDStatus.DUPLICATE
        upd.duplicate_of_id = original_upd_id
        upd.duplicate_checked_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(upd)
        
        return upd
    
    async def find_potential_duplicates(
        self,
        upd_id: int,
        tolerance_days: int = 3
    ) -> List[MaterialCost]:
        """
        Поиск потенциальных дубликатов для УПД
        
        Ищет УПД с похожим номером документа и датой в пределах tolerance_days
        
        Args:
            upd_id: ID УПД для проверки
            tolerance_days: допустимое отклонение по дате (дни)
            
        Returns:
            Список потенциальных дубликатов
        """
        upd = await self.get_upd_by_id(upd_id)
        if not upd:
            raise ValueError(f"УПД {upd_id} не найден")
        
        from datetime import timedelta
        date_from = upd.document_date - timedelta(days=tolerance_days)
        date_to = upd.document_date + timedelta(days=tolerance_days)
        
        query = select(MaterialCost).where(
            MaterialCost.id != upd_id,
            MaterialCost.document_number == upd.document_number,
            MaterialCost.document_date >= date_from,
            MaterialCost.document_date <= date_to,
            MaterialCost.status != UPDStatus.DUPLICATE
        )
        
        # Если есть ИНН, добавляем его в условия
        if upd.supplier_inn:
            query = query.where(MaterialCost.supplier_inn == upd.supplier_inn)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def log_distribution_history(
        self,
        material_cost_id: int,
        user_id: int,
        action: str,
        old_distribution: Optional[dict] = None,
        new_distribution: dict = None,
        description: Optional[str] = None
    ) -> UPDDistributionHistory:
        """
        Логирование изменений в распределении УПД
        
        Args:
            material_cost_id: ID УПД
            user_id: ID пользователя
            action: тип действия (CREATE, UPDATE, DELETE)
            old_distribution: старое распределение (для UPDATE/DELETE)
            new_distribution: новое распределение
            description: описание изменения
            
        Returns:
            Созданная запись истории
        """
        history = UPDDistributionHistory(
            material_cost_id=material_cost_id,
            user_id=user_id,
            action=action,
            old_distribution=old_distribution,
            new_distribution=new_distribution,
            description=description
        )
        
        self.db.add(history)
        await self.db.flush()
        
        return history
    
    async def get_distribution_history(
        self,
        upd_id: int,
        limit: int = 50
    ) -> List[UPDDistributionHistory]:
        """
        Получение истории распределения УПД
        
        Args:
            upd_id: ID УПД
            limit: максимальное количество записей
            
        Returns:
            Список записей истории
        """
        query = (
            select(UPDDistributionHistory)
            .where(UPDDistributionHistory.material_cost_id == upd_id)
            .order_by(UPDDistributionHistory.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def redistribute_upd(
        self,
        upd_id: int,
        user_id: int,
        new_distributions: List[DistributionItemCreate]
    ) -> MaterialCost:
        """
        Корректировка распределения УПД
        
        Args:
            upd_id: ID УПД
            user_id: ID пользователя, выполняющего корректировку
            new_distributions: новое распределение
            
        Returns:
            Обновлённый MaterialCost
            
        Raises:
            ValueError: если УПД не найден или в статусе ARCHIVED
        """
        # Загрузка УПД
        upd = await self.get_upd_by_id(upd_id)
        if not upd:
            raise ValueError(f"УПД с ID {upd_id} не найден")
        
        if upd.status == UPDStatus.ARCHIVED:
            raise ValueError("Нельзя изменить распределение архивированного УПД")
        
        if upd.status == UPDStatus.DUPLICATE:
            raise ValueError("Нельзя изменить распределение дубликата УПД")
        
        # Валидация новых распределений
        await self._validate_distributions(upd, new_distributions)
        
        # Сохранение старого распределения для истории
        old_distributions_query = select(UPDDistribution).where(
            UPDDistribution.material_cost_id == upd_id
        )
        old_distributions_result = await self.db.execute(old_distributions_query)
        old_distributions = list(old_distributions_result.scalars().all())
        
        old_distribution_data = {
            "distributions": [
                {
                    "material_cost_item_id": d.material_cost_item_id,
                    "material_request_id": d.material_request_id,
                    "cost_object_id": d.cost_object_id,
                    "distributed_quantity": float(d.distributed_quantity),
                    "distributed_amount": float(d.distributed_amount)
                }
                for d in old_distributions
            ],
            "total_amount": sum(d.distributed_amount for d in old_distributions)
        }
        
        # Удаление старых распределений
        for old_dist in old_distributions:
            await self.db.delete(old_dist)
        
        # Удаление старых записей затрат
        from sqlalchemy import delete
        await self.db.execute(
            delete(CostEntry).where(
                CostEntry.reference_type == "MaterialCost",
                CostEntry.reference_id == upd_id
            )
        )
        
        # Создание новых распределений
        total_distributed = Decimal("0")
        
        for dist in new_distributions:
            # Получение строки УПД
            item = next(
                (i for i in upd.items if i.id == dist.material_cost_item_id),
                None
            )
            if not item:
                raise ValueError(f"Строка УПД {dist.material_cost_item_id} не найдена")
            
            # Определение объекта учета
            cost_object_id = dist.cost_object_id
            if dist.material_request_id:
                request = await self.db.get(MaterialRequest, dist.material_request_id)
                if request:
                    cost_object_id = request.cost_object_id
            
            # Создание записи распределения
            distribution = UPDDistribution(
                material_cost_id=upd.id,
                material_cost_item_id=dist.material_cost_item_id,
                material_request_id=dist.material_request_id,
                cost_object_id=cost_object_id,
                distributed_quantity=dist.distributed_quantity,
                distributed_amount=dist.distributed_amount
            )
            self.db.add(distribution)
            
            # Создание записи затрат
            if cost_object_id:
                cost_entry = CostEntry(
                    type="material",
                    cost_object_id=cost_object_id,
                    date=upd.document_date,
                    amount=dist.distributed_amount,
                    description=f"УПД {upd.document_number}: {item.product_name}",
                    reference_type="MaterialCost",
                    reference_id=upd.id
                )
                self.db.add(cost_entry)
            
            total_distributed += dist.distributed_amount
        
        # Новое распределение для истории
        new_distribution_data = {
            "distributions": [
                {
                    "material_cost_item_id": d.material_cost_item_id,
                    "material_request_id": d.material_request_id,
                    "cost_object_id": d.cost_object_id,
                    "distributed_quantity": float(d.distributed_quantity),
                    "distributed_amount": float(d.distributed_amount)
                }
                for d in new_distributions
            ],
            "total_amount": float(total_distributed)
        }
        
        # Логирование в историю
        await self.log_distribution_history(
            material_cost_id=upd_id,
            user_id=user_id,
            action="UPDATE",
            old_distribution=old_distribution_data,
            new_distribution=new_distribution_data,
            description=f"Корректировка распределения УПД №{upd.document_number}"
        )
        
        await self.db.commit()
        await self.db.refresh(upd)
        
        return upd
