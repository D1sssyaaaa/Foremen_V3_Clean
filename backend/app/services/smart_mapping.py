import logging
import asyncio
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import EstimateItem, CostObject
from app.materials.models_mapping import ProductAlias

# Попытка импорта rapidfuzz для быстрого нечеткого поиска,
# иначе используем стандартный difflib (медленнее, но работает из коробки)
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

logger = logging.getLogger(__name__)

class SmartMappingService:
    """
    Сервис для умного маппинга товаров из УПД в позиции сметы.
    Использует:
    1. Точное совпадение через ProductAlias (обучаемая таблица)
    2. Нечеткий поиск по названиям (Fuzzy Search)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_best_match(
        self,
        product_name: str,
        supplier_inn: Optional[str] = None,
        cost_object_id: Optional[int] = None,
        min_confidence: float = 70.0
    ) -> Optional[Dict[str, Any]]:
        """
        Поиск лучшего соответствия для товара из УПД.
        
        Args:
            product_name: Название товара из УПД
            supplier_inn: ИНН поставщика (для контекста)
            cost_object_id: ID объекта (для сужения поиска по смете)
            min_confidence: Минимальный порог уверенности (0-100)
            
        Returns:
            Словарь с результатом или None:
            {
                "estimate_item_id": int,
                "confidence": float,
                "source": "alias_exact" | "alias_fuzzy" | "estimate_fuzzy",
                "matched_name": str
            }
        """
        product_name_clean = product_name.strip()
        
        # 1. Поиск точного совпадения в ProductAlias
        # Сначала с учетом ИНН поставщика
        if supplier_inn:
            alias = await self._find_alias(product_name_clean, supplier_inn)
            if alias and alias.estimate_item_id:
                obj_id, obj_name = await self._get_item_details(alias.estimate_item_id)
                return {
                    "estimate_item_id": alias.estimate_item_id,
                    "suggested_cost_object_id": obj_id,
                    "suggested_cost_object_name": obj_name,
                    "confidence": 100.0,
                    "source": "alias_exact_supplier",
                    "matched_name": alias.canonical_name
                }
        
        # Затем без учета ИНН (глобальный алиас)
        alias = await self._find_alias(product_name_clean, None)
        if alias and alias.estimate_item_id:
            obj_id, obj_name = await self._get_item_details(alias.estimate_item_id)
            return {
                "estimate_item_id": alias.estimate_item_id,
                "suggested_cost_object_id": obj_id,
                "suggested_cost_object_name": obj_name,
                "confidence": 95.0, # Чуть меньше 100, т.к. другой поставщик
                "source": "alias_exact_global",
                "matched_name": alias.canonical_name
            }

        # Если объект не указан, мы не можем искать по смете эффективно
        if not cost_object_id:
            return None

        # 2. Получаем все позиции сметы для объекта
        # Получаем имя объекта для ответа
        cost_object_name = await self._get_object_name(cost_object_id)
        estimate_items = await self._get_estimate_items(cost_object_id)
        if not estimate_items:
            return None
            
        estimate_names = [item.name for item in estimate_items]
        estimate_map = {item.name: item.id for item in estimate_items}
        
        # 3. Нечеткий поиск
        match_name, score = self._fuzzy_search(product_name_clean, estimate_names)
        
        if score >= min_confidence:
            return {
                "estimate_item_id": estimate_map[match_name],
                "suggested_cost_object_id": cost_object_id,
                "suggested_cost_object_name": cost_object_name,
                "confidence": float(score),
                "source": "estimate_fuzzy",
                "matched_name": match_name
            }
            
        return None

    async def learn_mapping(
        self,
        product_name: str,
        estimate_item_id: int,
        supplier_inn: Optional[str] = None,
        is_manual: bool = True
    ) -> ProductAlias:
        """
        Запоминание выбора пользователя (обучение)
        """
        product_name_clean = product_name.strip()
        
        # Получаем имя из сметы для canonical_name
        est_item = await self.db.get(EstimateItem, estimate_item_id)
        canonical_name = est_item.name if est_item else product_name_clean
        
        # Ищем существующий алиас
        query = select(ProductAlias).where(
            ProductAlias.supplier_name == product_name_clean,
            ProductAlias.supplier_inn == supplier_inn
        )
        result = await self.db.execute(query)
        alias = result.scalar_one_or_none()
        
        if alias:
            # Обновляем существующий
            alias.estimate_item_id = estimate_item_id
            alias.canonical_name = canonical_name
            alias.use_count += 1
            if is_manual:
                alias.confidence = 100.0
        else:
            # Создаем новый
            alias = ProductAlias(
                supplier_name=product_name_clean,
                canonical_name=canonical_name,
                estimate_item_id=estimate_item_id,
                supplier_inn=supplier_inn,
                confidence=100.0 if is_manual else 80.0,
                use_count=1
            )
            self.db.add(alias)
            
        await self.db.commit()
        await self.db.refresh(alias)
        return alias

    async def _find_alias(self, name: str, inn: Optional[str]) -> Optional[ProductAlias]:
        query = select(ProductAlias).where(
            ProductAlias.supplier_name == name,
            ProductAlias.supplier_inn == inn
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_item_details(self, estimate_item_id: int) -> Tuple[Optional[int], Optional[str]]:
        """Получение ID и имени объекта для позиции сметы"""
        stmt = select(EstimateItem).options(selectinload(EstimateItem.cost_object)).where(EstimateItem.id == estimate_item_id)
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()
        if item and item.cost_object:
            return item.cost_object_id, item.cost_object.name
        return None, None

    async def _get_object_name(self, cost_object_id: int) -> Optional[str]:
        """Получение имени объекта по ID"""
        obj = await self.db.get(CostObject, cost_object_id)
        return obj.name if obj else None

    async def _get_estimate_items(self, cost_object_id: int) -> List[EstimateItem]:
        query = select(EstimateItem).where(EstimateItem.cost_object_id == cost_object_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _fuzzy_search(self, query: str, choices: List[str]) -> Tuple[str, float]:
        """
        Возвращает (лучшее_совпадение, счет_0_100)
        """
        if not choices:
            return "", 0.0

        if HAS_RAPIDFUZZ:
            # extractOne возвращает (match, score, index)
            result = process.extractOne(query, choices, scorer=fuzz.token_sort_ratio)
            if result:
                return result[0], result[1]
            return "", 0.0
        else:
            # Fallback: difflib
            matches = difflib.get_close_matches(query, choices, n=1, cutoff=0.0)
            if matches:
                match = matches[0]
                # Вычисляем score вручную для совместимости
                ratio = difflib.SequenceMatcher(None, query, match).ratio()
                return match, ratio * 100.0
            return "", 0.0
