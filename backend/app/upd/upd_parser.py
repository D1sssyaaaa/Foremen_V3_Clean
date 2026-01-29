"""
Парсер УПД (Универсальный Передаточный Документ) XML
Поддерживает форматы 5.01 и 5.03, различные генераторы
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class UPDParseError(Exception):
    """Исключение при ошибке парсинга УПД"""
    pass


class IssueSeverity(str, Enum):
    """Уровень критичности проблемы парсинга"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ParsingIssue:
    """Описание проблемы при парсинге"""
    severity: IssueSeverity
    element: str
    message: str
    generator: Optional[str] = None
    value: Optional[str] = None


@dataclass
class UPDItem:
    """Строка товара/услуги из УПД"""
    product_name: str
    quantity: Decimal
    unit: str
    price: Decimal
    amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total_with_vat: Decimal
    okei_code: Optional[str] = None


@dataclass
class UPDDocument:
    """Распарсенный УПД документ"""
    document_number: str
    document_date: datetime
    supplier_name: str
    total_amount: Decimal
    total_vat: Decimal
    total_with_vat: Decimal
    supplier_inn: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_inn: Optional[str] = None
    items: List[UPDItem] = field(default_factory=list)
    parsing_issues: List[ParsingIssue] = field(default_factory=list)
    generator: Optional[str] = None
    format_version: Optional[str] = None


# Словарь кодов ОКЕИ -> единицы измерения
OKEI_UNITS = {
    "796": "шт",
    "006": "м",
    "055": "м²",
    "113": "м³",
    "166": "кг",
    "168": "т",
    "356": "ч",
    "112": "л",
    "778": "упак",
    "715": "компл",
    "704": "набор",
    "111": "пог.м",
    "039": "км",
    "163": "г",
    "359": "сут",
    "360": "нед",
    "362": "мес",
    "365": "год",
}


def convert_okei_to_unit(okei_code: Optional[str]) -> str:
    """Преобразование кода ОКЕИ в единицу измерения"""
    if not okei_code:
        return "шт"
    
    unit = OKEI_UNITS.get(okei_code)
    if unit:
        return unit
    
    # Fallback: возвращаем код как есть
    return okei_code


class UPDParser:
    """Парсер XML файлов УПД"""
    
    def __init__(self):
        self.issues: List[ParsingIssue] = []
        self.generator: Optional[str] = None
    
    def parse(self, xml_content: bytes) -> UPDDocument:
        """
        Парсинг XML УПД документа
        
        Args:
            xml_content: содержимое XML файла в байтах
            
        Returns:
            UPDDocument с распарсенными данными
            
        Raises:
            UPDParseError: если XML невалидный или критические поля отсутствуют
        """
        self.issues = []
        self.generator = None
        
        try:
            # Парсинг с указанием кодировки windows-1251
            xml_str = xml_content.decode('windows-1251')
            root = ET.fromstring(xml_str)
        except Exception as e:
            raise UPDParseError(f"Ошибка парсинга XML: {str(e)}")
        
        # Определение генератора
        self._detect_generator(root)
        
        # Извлечение основных данных
        document_number = self._extract_document_number(root)
        document_date = self._extract_document_date(root)
        supplier_name, supplier_inn = self._extract_supplier(root)
        buyer_name, buyer_inn = self._extract_buyer(root)
        items = self._extract_items(root)
        
        # Валидация обязательных полей
        if not document_number:
            raise UPDParseError("Не найден номер документа")
        if not document_date:
            raise UPDParseError("Не найдена дата документа")
        if not items:
            raise UPDParseError("Не найдено ни одной строки товаров/услуг")
        
        # Расчет итоговых сумм
        total_amount = sum(item.amount for item in items)
        total_vat = sum(item.vat_amount for item in items)
        total_with_vat = sum(item.total_with_vat for item in items)
        
        return UPDDocument(
            document_number=document_number,
            document_date=document_date,
            supplier_name=supplier_name or "Не указан",
            supplier_inn=supplier_inn,
            buyer_name=buyer_name,
            buyer_inn=buyer_inn,
            total_amount=total_amount,
            total_vat=total_vat,
            total_with_vat=total_with_vat,
            items=items,
            parsing_issues=self.issues,
            generator=self.generator,
            format_version=self._extract_format_version(root)
        )
    
    def _detect_generator(self, root: ET.Element) -> None:
        """Определение генератора УПД"""
        # Поиск элементов с информацией о программе
        for elem in root.iter():
            text = elem.text or ""
            
            if "Elewise" in text or "LegalDoc" in text:
                self.generator = "Elewise LegalDoc"
                return
            elif "1С:Бухгалтерия" in text or "1C:" in text:
                self.generator = "1С:Бухгалтерия"
                return
            elif "Diadoc" in text:
                self.generator = "Diadoc"
                return
            elif "VO2_xslt" in text:
                self.generator = "VO2_xslt"
                return
        
        # Проверка по атрибутам
        if root.find(".//*[@НаимЭконСубСост]") is not None:
            self.generator = "Unknown (формат 5.01)"
        else:
            self.generator = "Unknown"
        
        self.issues.append(ParsingIssue(
            severity=IssueSeverity.INFO,
            element="root",
            message=f"Определен генератор: {self.generator}",
            generator=self.generator
        ))
    
    def _extract_format_version(self, root: ET.Element) -> Optional[str]:
        """Извлечение версии формата"""
        version_elem = root.find(".//*[@ВерсФорм]")
        if version_elem is not None:
            return version_elem.get("ВерсФорм")
        return None
    
    def _extract_document_number(self, root: ET.Element) -> Optional[str]:
        """Извлечение номера документа с fallback"""
        # Попытка 1: НомерСчФ
        elem = root.find(".//*[@НомерСчФ]")
        if elem is not None:
            number = elem.get("НомерСчФ")
            if number:
                return number
        
        # Fallback: НомерДок
        elem = root.find(".//*[@НомерДок]")
        if elem is not None:
            number = elem.get("НомерДок")
            if number:
                self.issues.append(ParsingIssue(
                    severity=IssueSeverity.WARNING,
                    element="document_number",
                    message="Номер извлечен из НомерДок (fallback)",
                    value=number
                ))
                return number
        
        return None
    
    def _extract_document_date(self, root: ET.Element) -> Optional[datetime]:
        """Извлечение даты документа с fallback"""
        # Попытка 1: ДатаСчФ
        elem = root.find(".//*[@ДатаСчФ]")
        if elem is not None:
            date_str = elem.get("ДатаСчФ")
            if date_str:
                try:
                    return datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    pass
        
        # Fallback: ДатаДок
        elem = root.find(".//*[@ДатаДок]")
        if elem is not None:
            date_str = elem.get("ДатаДок")
            if date_str:
                try:
                    self.issues.append(ParsingIssue(
                        severity=IssueSeverity.WARNING,
                        element="document_date",
                        message="Дата извлечена из ДатаДок (fallback)",
                        value=date_str
                    ))
                    return datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    pass
        
        return None
    
    def _extract_supplier(self, root: ET.Element) -> tuple[Optional[str], Optional[str]]:
        """Извлечение имени и ИНН поставщика"""
        # Поиск элемента Продавец/Грузоотправитель
        supplier_elem = root.find(".//СвПрод")
        if supplier_elem is None:
            supplier_elem = root.find(".//СвПродавец")
        
        if supplier_elem is None:
            return None, None
        
        # Извлечение имени
        name_elem = supplier_elem.find(".//*[@НаимОрг]")
        if name_elem is None:
            name_elem = supplier_elem.find(".//*[@НаимЮЛ]")
        
        name = None
        if name_elem is not None:
            name = name_elem.get("НаимОрг") or name_elem.get("НаимЮЛ")
        
        # Обработка формата 1С: "ООО ... , ИНН/КПП ..."
        inn = None
        if name and self.generator == "1С:Бухгалтерия":
            if ", ИНН" in name or ",ИНН" in name:
                parts = name.split(",")
                name = parts[0].strip()
                # Извлечение ИНН регулярным выражением
                import re
                inn_match = re.search(r'ИНН[:\s]*(\d{10,12})', name)
                if inn_match:
                    inn = inn_match.group(1)
        
        # Если ИНН не найден в имени, ищем отдельно
        if not inn:
            inn_elem = supplier_elem.find(".//*[@ИННЮЛ]")
            if inn_elem is None:
                inn_elem = supplier_elem.find(".//*[@ИНН]")
            
            if inn_elem is not None:
                inn = inn_elem.get("ИННЮЛ") or inn_elem.get("ИНН")
        
        return name, inn
    
    def _extract_buyer(self, root: ET.Element) -> tuple[Optional[str], Optional[str]]:
        """Извлечение имени и ИНН покупателя"""
        buyer_elem = root.find(".//СвПокуп")
        if buyer_elem is None:
            return None, None
        
        # Извлечение имени
        name_elem = buyer_elem.find(".//*[@НаимОрг]")
        if name_elem is None:
            name_elem = buyer_elem.find(".//*[@НаимЮЛ]")
        
        name = None
        if name_elem is not None:
            name = name_elem.get("НаимОрг") or name_elem.get("НаимЮЛ")
        
        # Извлечение ИНН
        inn_elem = buyer_elem.find(".//*[@ИННЮЛ]")
        if inn_elem is None:
            inn_elem = buyer_elem.find(".//*[@ИНН]")
        
        inn = None
        if inn_elem is not None:
            inn = inn_elem.get("ИННЮЛ") or inn_elem.get("ИНН")
        
        return name, inn
    
    def _extract_items(self, root: ET.Element) -> List[UPDItem]:
        """Извлечение строк товаров/услуг с fallback"""
        items = []
        
        # Поиск всех элементов СведТов (стандартные товары)
        for item_elem in root.findall(".//СведТов"):
            item = self._parse_sved_tov(item_elem)
            if item:
                items.append(item)
        
        # Если не найдено, пробуем СведТовУслСч (услуги)
        if not items:
            for item_elem in root.findall(".//СведТовУслСч"):
                item = self._parse_sved_tov_usl_sch(item_elem)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_sved_tov(self, elem: ET.Element) -> Optional[UPDItem]:
        """Парсинг стандартной строки товара"""
        try:
            # Обязательные поля
            product_name = elem.get("НаимТов")
            if not product_name:
                return None
            
            # Количество и цена
            quantity_str = elem.get("КолТов", "0")
            price_str = elem.get("ЦенаТов", "0")
            
            quantity = Decimal(quantity_str.replace(",", "."))
            price = Decimal(price_str.replace(",", "."))
            
            # Единица измерения
            okei_code = elem.get("ОКЕИ")
            unit = convert_okei_to_unit(okei_code)
            
            # Суммы
            amount_str = elem.get("СтТовБезНДС") or elem.get("СтТовУчНал", "0")
            amount = Decimal(amount_str.replace(",", "."))
            
            # НДС
            vat_rate = self._extract_vat_rate(elem)
            vat_amount_str = elem.get("СумНал", "0")
            vat_amount = Decimal(vat_amount_str.replace(",", "."))
            
            # Итого с НДС
            total_with_vat_str = elem.get("СтТовУчНал", "0")
            total_with_vat = Decimal(total_with_vat_str.replace(",", "."))
            
            # Fallback для услуг без количества/цены
            if quantity == 0 and price == 0 and amount > 0:
                self.issues.append(ParsingIssue(
                    severity=IssueSeverity.WARNING,
                    element="item",
                    message=f"Товар '{product_name}' без КолТов/ЦенаТов, трактуется как услуга",
                    value=product_name
                ))
                quantity = Decimal("1")
                unit = "услуга"
                price = amount
            
            return UPDItem(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
                price=price,
                amount=amount,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                total_with_vat=total_with_vat,
                okei_code=okei_code
            )
        
        except (ValueError, TypeError, InvalidOperation) as e:
            self.issues.append(ParsingIssue(
                severity=IssueSeverity.ERROR,
                element="item",
                message=f"Ошибка парсинга строки: {str(e)}",
                value=str(elem.attrib)
            ))
            return None
    
    def _parse_sved_tov_usl_sch(self, elem: ET.Element) -> Optional[UPDItem]:
        """Парсинг строки услуг (формат без КолТов/ЦенаТов)"""
        try:
            product_name = elem.get("НаимТовУслСч")
            if not product_name:
                return None
            
            # Для услуг используем количество = 1
            quantity = Decimal("1")
            unit = "услуга"
            
            # Сумма
            amount_str = elem.get("СтТовБезНДС") or elem.get("СтТовУчНал", "0")
            amount = Decimal(amount_str.replace(",", "."))
            price = amount  # Для услуг цена = сумма
            
            # НДС
            vat_rate = self._extract_vat_rate(elem)
            vat_amount_str = elem.get("СумНал", "0")
            vat_amount = Decimal(vat_amount_str.replace(",", "."))
            
            # Итого
            total_with_vat_str = elem.get("СтТовУчНал", "0")
            total_with_vat = Decimal(total_with_vat_str.replace(",", "."))
            
            self.issues.append(ParsingIssue(
                severity=IssueSeverity.INFO,
                element="item",
                message=f"Услуга '{product_name}' без количества, установлено qty=1",
                value=product_name
            ))
            
            return UPDItem(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
                price=price,
                amount=amount,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                total_with_vat=total_with_vat,
                okei_code=None
            )
        
        except (ValueError, TypeError, InvalidOperation) as e:
            self.issues.append(ParsingIssue(
                severity=IssueSeverity.ERROR,
                element="item",
                message=f"Ошибка парсинга услуги: {str(e)}",
                value=str(elem.attrib)
            ))
            return None
    
    
    def _extract_vat_rate(self, elem: ET.Element) -> Decimal:
        """Извлечение ставки НДС с fallback"""
        # Попытка 1: НалСт
        vat_str = elem.get("НалСт")
        if vat_str:
            # Обработка "без НДС"
            if "без" in vat_str.lower():
                return Decimal("0")
                
            try:
                return Decimal(vat_str.replace(",", "."))
            except (ValueError, InvalidOperation):
                pass
        
        # Fallback 1: НДС
        vat_str = elem.get("НДС")
        if vat_str:
            try:
                self.issues.append(ParsingIssue(
                    severity=IssueSeverity.INFO,
                    element="vat_rate",
                    message="НДС извлечен из атрибута НДС (fallback)",
                    value=vat_str
                ))
                return Decimal(vat_str.replace(",", "."))
            except (ValueError, InvalidOperation):
                pass
        
        # Fallback 2: дефолт 20%
        self.issues.append(ParsingIssue(
            severity=IssueSeverity.WARNING,
            element="vat_rate",
            message="НДС не найден, используется дефолт 20%",
            value="20"
        ))
        return Decimal("20")
