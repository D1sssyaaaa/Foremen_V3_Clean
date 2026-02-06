"""
Парсер УПД XML файлов (реальная структура Elewise LegalDoc)

ВЕРСИЯ: 2.0
Дата: 2026-01-24
Особенности:
  - Поддержка генераторов: 1С:Предприятие 8, Elewise LegalDoc, Diadoc 1.0, VO2_xslt
  - Обработка service invoice формата (СведТов без КолТов/ЦенаТов)
  - Расширенные коды ОКЕЙ (356 = час, 796 = штуки, и др.)
  - Graceful degradation - парсер продолжает работу при ошибках
  - Логирование проблемных элементов
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

# Словарь кодов ОКЕИ (Общероссийский классификатор единиц измерения) - полный набор
OKEI_UNITS = {
    # Единицы длины (основные коды)
    '006': 'м',        # Метры
    '7': 'мм',         # Миллиметры
    '8': 'см',         # Сантиметры
    '9': 'дм',         # Дециметры
    '10': 'м',         # Метры
    '11': 'км',        # Километры
    '12': 'дюйм',      # Дюймы
    '13': 'фут',       # Футы
    '14': 'ярд',       # Ярды
    '15': 'миля',      # Мили
    '16': 'морс.м',    # Морские мили
    
    # Штучные единицы
    '778': 'м.п.',     # Метры погонные (метры линейные)
    '796': 'шт',       # Штуки
    '797': 'компл',    # Комплекты
    '798': 'пара',     # Пары
    '799': 'набор',    # Наборы
    '800': 'упак',     # Упаковки
    '801': 'ящ',       # Ящики
    '802': 'мешок',    # Мешки
    '803': 'бочка',    # Бочки
    '804': 'рулон',    # Рулоны
    '805': 'бак',      # Баки
    '806': 'бутыль',   # Бутыли
    '807': 'канистра', # Канистры
    '808': 'баллон',   # Баллоны газовые
    '809': 'кассета',  # Кассеты
    '810': 'картридж', # Картриджи
    '811': 'тюбик',    # Тюбики
    '812': 'флакон',   # Флаконы
    '813': 'банка',    # Банки
    '814': 'коробка',  # Коробки
    '815': 'пакет',    # Пакеты
    '816': 'лист',     # Листы
    '817': 'рама',     # Рамы
    '818': 'поддон',   # Поддоны
    '819': 'конт',     # Контейнеры
    '820': 'кат',      # Катушки
    '821': 'бобина',   # Бобины
    '822': 'барабан',  # Барабаны
    '823': 'спираль',  # Спирали
    '824': 'рейка',    # Рейки
    '825': 'планка',   # Планки
    '826': 'плита',    # Плиты
    '827': 'доска',    # Доски
    '828': 'панель',   # Панели
    '829': 'ограда',   # Ограды
    '830': 'перегородка', # Перегородки
    '831': 'направляющая', # Направляющие
    '832': 'опора',    # Опоры
    '833': 'монтаж',   # Монтажные единицы
    '834': 'блок',     # Блоки
    '835': 'башня',    # Башни
    '836': 'мост',     # Мосты
    '837': 'секция',   # Секции
    '838': 'кровля',   # Кровли
    '839': 'обшивка',  # Обшивки
    '840': 'клапан',   # Клапаны
    '841': 'вентиль',  # Вентили
    '842': 'кран',     # Краны
    '843': 'насос',    # Насосы
    '844': 'компрессор', # Компрессоры
    '845': 'вентилятор', # Вентиляторы
    '846': 'фильтр',   # Фильтры
    '847': 'реле',     # Реле
    '848': 'выключатель', # Выключатели
    '849': 'предохранитель', # Предохранители
    '850': 'резистор', # Резисторы
    '851': 'конденсатор', # Конденсаторы
    '852': 'катушка',  # Катушки индуктивности
    '853': 'трансформатор', # Трансформаторы
    '854': 'лампа',    # Лампы
    '855': 'светильник', # Светильники
    '856': 'свеча',    # Свечи зажигания
    '857': 'батарея',  # Батареи
    '858': 'аккумулятор', # Аккумуляторы
    '859': 'генератор', # Генераторы
    '860': 'двигатель', # Двигатели
    '861': 'редуктор', # Редукторы
    '862': 'муфта',    # Муфты
    '863': 'подшипник', # Подшипники
    '864': 'сальник',  # Сальники
    '865': 'прокладка', # Прокладки
    '866': 'уплотнитель', # Уплотнители
    '867': 'шайба',    # Шайбы
    '868': 'гайка',    # Гайки
    '869': 'болт',     # Болты
    '870': 'винт',     # Винты
    '871': 'шуруп',    # Шурупы
    '872': 'гвоздь',   # Гвозди
    '873': 'дюбель',   # Дюбели
    '874': 'анкер',    # Анкеры
    '875': 'пластина', # Пластины
    '876': 'полоса',   # Полосы металлические
    '877': 'прут',     # Пруты
    '878': 'труба',    # Трубы
    '879': 'уголок',   # Уголки
    '880': 'швеллер',  # Швеллеры
    '881': 'двутавр',  # Двутавры
    '882': 'пак',      # Паки/пачки
    '883': 'стопка',   # Стопки
    '884': 'связка',   # Связки
    '885': 'порция',   # Порции
    '886': 'страница', # Страницы
    
    # Единицы массы
    '1': 'мг',         # Миллиграммы
    '2': 'г',          # Граммы
    '3': 'кг',         # Килограммы
    '4': 'т',          # Тонны
    '5': 'ц',          # Центнеры
    '6': 'гр',         # Гроссы (144 шт)
    '30': 'дт',        # Дециграммы
    '31': 'т',         # Тонны метрические
    
    # Единицы длины
    # Единицы массы
    '1': 'мг',         # Миллиграммы
    '2': 'г',          # Граммы
    '3': 'кг',         # Килограммы
    '4': 'т',          # Тонны
    '5': 'ц',          # Центнеры
    '6': 'гр',         # Гроссы (144 шт)
    '30': 'дт',        # Дециграммы
    '31': 'т',         # Тонны метрические
    
    # Единицы площади
    '17': 'см2',       # Квадратные сантиметры
    '18': 'м2',        # Квадратные метры
    '19': 'км2',       # Квадратные километры
    '20': 'га',        # Гектары
    '21': 'ар',        # Ары
    '22': 'дюйм2',     # Квадратные дюймы
    '23': 'фут2',      # Квадратные футы
    '32': 'мм2',       # Квадратные миллиметры
    
    # Единицы времени
    '38': 'ч',         # Часы
    '354': 'сек',      # Секунды
    '355': 'мин',      # Минуты
    '356': 'ч',        # Часы (альтернативный код ОКЕИ)
    
    # Единицы времени
    '36': 'сек',       # Секунды
    '37': 'мин',       # Минуты
    '38': 'ч',         # Часы
    '39': 'сут',       # Сутки
    '40': 'неделя',    # Недели
    '41': 'месяц',     # Месяцы
    '42': 'год',       # Годы
    '43': 'десятилетие', # Десятилетия
    
    # Единицы температуры
    '44': 'К',         # Кельвины
    '45': '°C',        # Градусы Цельсия
    '46': '°F',        # Градусы Фаренгейта
    
    # Единицы энергии и мощности
    '47': 'кал',       # Калории
    '48': 'ккал',      # Килокалории
    '49': 'Дж',        # Джоули
    '50': 'кДж',       # Килоджоули
    '51': 'МДж',       # Мегаджоули
    '52': 'ГДж',       # Гигаджоули
    '53': 'эрг',       # Эрги
    '54': 'Вт',        # Ватты
    '55': 'кВт',       # Киловатты
    '56': 'МВт',       # Мегаватты
    '57': 'ГВт',       # Гигаватты
    '58': 'кВА',       # Киловольт-амперы
    '59': 'МВА',       # Мегавольт-амперы
    '60': 'кВАр',      # Киловольт-амперы реактивные
    '61': 'МВАр',      # Мегавольт-амперы реактивные
    
    # Единицы электроэнергии
    '62': 'кВ-ч',      # Киловатт-часы
    '63': 'МВ-ч',      # Мегаватт-часы
    '64': 'ГВ-ч',      # Гигаватт-часы
    '65': 'кВА-ч',     # Киловольт-ампер-часы
    '66': 'кВАр-ч',    # Киловольт-ампер-реактивные-часы
    
    # Единицы напряжения и тока
    '67': 'В',         # Вольты
    '68': 'кВ',        # Киловольты
    '69': 'мВ',        # Милливольты
    '70': 'А',         # Амперы
    '71': 'кА',        # Килоамперы
    '72': 'мА',        # Миллиамперы
    '73': 'Ом',        # Омы
    '74': 'кОм',       # Килоомы
    '75': 'МОм',       # Мегаомы
    '76': 'См',        # Сименсы
    '77': 'Ф',         # Фарады
    '78': 'мкФ',       # Микрофарады
    '79': 'пФ',        # Пикофарады
    '80': 'Гн',        # Генри
    '81': 'мГн',       # Миллигенри
    '82': 'мкГн',      # Микрогенри
    
    # Единицы частоты
    '83': 'Гц',        # Герцы
    '84': 'кГц',       # Килогерцы
    '85': 'МГц',       # Мегагерцы
    '86': 'ГГц',       # Гигагерцы
    '87': 'об/мин',    # Обороты в минуту
    '88': 'об/сек',    # Обороты в секунду
    
    # Единицы силы и давления
    '89': 'Н',         # Ньютоны
    '90': 'кН',        # Килоньютоны
    '91': 'МН',        # Меганьютоны
    '92': 'Па',        # Паскали
    '93': 'кПа',       # Килопаскали
    '94': 'МПа',       # Мегапаскали
    '95': 'ГПа',       # Гигапаскали
    '96': 'атм',       # Атмосферы
    '97': 'бар',       # Бары
    '98': 'торр',      # Торры
    '99': 'мм рт.ст',  # Миллиметры ртутного столба
    
    # Единицы концентрации
    '100': 'моль/л',   # Молярность
    '101': 'г/л',      # Граммы на литр
    '102': 'г/см3',    # Граммы на кубический сантиметр
    '103': 'кг/м3',    # Килограммы на кубический метр
    '104': 'мг/л',     # Миллиграммы на литр
    
    # Единицы освещения
    '105': 'кд',       # Канделы
    '106': 'люм',      # Люмены
    '107': 'люкс',     # Люксы
    
    # Единицы звука
    '108': 'Бел',      # Белы
    '109': 'дБ',       # Децибелы
    
    # Единицы радиоактивности
    '110': 'Бк',       # Беккерели
    '111': 'Кюри',     # Кюри
    '112': 'Гр',       # Греи
    '113': 'Зв',       # Зиверты
    
    # Дополнительные единицы
    '114': 'проц',     # Проценты
    '115': 'ppm',      # Миллионные доли
    '116': 'ед',       # Единицы (условные)
    '117': 'усл.банка', # Условные банки
    '118': 'усл.кас',  # Условные кассеты
    '119': 'усл.компл', # Условные комплекты
    '120': 'условн.',  # Условные единицы
}

# Словарь сокращений для типов организаций
ORG_ABBREVIATIONS = {
    'Общество с ограниченной ответственностью': 'ООО',
    'Акционерное общество': 'АО',
    'Закрытое акционерное общество': 'ЗАО',
    'Открытое акционерное общество': 'ОАО',
    'Полное товарищество': 'ПТ',
    'Коммандитное товарищество': 'КТ',
    'Производственный кооператив': 'ПК',
    'Потребительский кооператив': 'ПотК',
    'Публичное акционерное общество': 'ПАО',
    'Индивидуальный предприниматель': 'ИП',
}


def convert_okei_to_unit(okei_code: str) -> str:
    """Преобразует код ОКЕИ в название единицы измерения"""
    return OKEI_UNITS.get(okei_code, okei_code)


def shorten_org_name(name: str) -> str:
    """Сокращает название организации (ООО вместо полного названия)"""
    if not name:
        return name
    
    # Пробуем найти в начале строки полное название организации
    for full_name, short_name in ORG_ABBREVIATIONS.items():
        if name.startswith(full_name):
            # Заменяем полное название на сокращение
            rest = name[len(full_name):].strip()
            if rest.startswith('"'):
                return short_name + ' ' + rest
            elif rest:
                return short_name + ' ' + rest
            else:
                return short_name
    
    return name


@dataclass
class UPDItem:
    """Товарная позиция в УПД"""
    product_name: str
    quantity: float
    unit: str
    unit_price: float
    sum_without_vat: float
    vat_rate: float
    vat_amount: float
    

@dataclass
class ParsingIssue:
    """Проблема при парсинге - для отслеживания ошибок"""
    severity: str  # 'warning', 'error', 'info'
    element: str  # Название элемента/атрибута
    message: str  # Описание проблемы
    generator: str = ''  # Какой генератор её вызвал
    value: str = ''  # Что мы получили вместо ожидаемого

@dataclass
class UPDDocument:
    """Распарсенный документ УПД"""
    document_number: str
    document_date: str
    supplier_name: str
    supplier_inn: str
    items: List[UPDItem]
    total_without_vat: float
    total_vat: float
    total_with_vat: float
    item_count: int
    xml_version: str  # 5.01, 5.03
    generator: str  # Elewise, VO2, Diadoc, 1С
    parsing_status: str  # "SUCCESS" или описание ошибки
    parsing_issues: List[dict] = None  # Список проблем при парсинге


class UPDParser:
    """Парсер УПД (реальная структура Elewise)"""
    PARSER_VERSION = '2.0'
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.result = None
        self.parsing_issues = []  # Отслеживаем проблемы
        
    def add_issue(self, severity: str, element: str, message: str, generator: str = '', value: str = ''):
        """Добавляет информацию о проблеме при парсинге"""
        self.parsing_issues.append({
            'severity': severity,
            'element': element,
            'message': message,
            'generator': generator,
            'value': value
        })
        
    def parse(self) -> UPDDocument:
        """Парсит файл УПД"""
        try:
            # 1. Прочитать файл
            with open(self.file_path, 'r', encoding='windows-1251') as f:
                content = f.read()
            
            # 2. Парсить XML
            root = ET.fromstring(content)
            
            # 3. Найти Документ
            doc_elem = root.find('.//Документ')
            if doc_elem is None:
                self.add_issue('error', 'Документ', 'Элемент Документ не найден в XML')
                raise ValueError("Документ не найден")
            
            # 4. Получить версию и генератор
            xml_version = root.get('ВерсияФормата', '5.01')
            generator = self._detect_generator(root)
            
            # 5. Извлечь номер и дату счета (поддержка обеих версий 5.01 и 5.03)
            schet_elem = doc_elem.find('СвСчФакт')
            if schet_elem is None:
                schet_elem = doc_elem.find('.//СвСчФакт')
            
            doc_number = 'UNKNOWN'
            doc_date = ''
            if schet_elem is not None:
                # Версия 5.01 использует НомерСчФ, версия 5.03 использует НомерДок
                doc_number = schet_elem.get('НомерСчФ') or schet_elem.get('НомерДок', 'UNKNOWN')
                doc_date = schet_elem.get('ДатаСчФ') or schet_elem.get('ДатаДок', '')
                
                if doc_number == 'UNKNOWN':
                    self.add_issue('warning', 'СвСчФакт', 
                                 'Не найдены атрибуты НомерСчФ/НомерДок', generator)
            else:
                self.add_issue('warning', 'СвСчФакт', 
                             'Элемент СвСчФакт не найден', generator)
            
            # 6. Извлечь информацию о поставщике
            supplier_name, supplier_inn = self._extract_supplier(doc_elem, generator)
            
            # 7. Извлечь товары
            items = self._extract_items(doc_elem, generator)
            
            # 8. Извлечь итоги
            total_without_vat, total_vat, total_with_vat = self._extract_totals(doc_elem)
            
            # Если есть проблемы с товарами, отметим это
            if len(items) == 0:
                self.add_issue('info', 'СведТов', 
                             'Товары/услуги не найдены в документе', generator)
            
            doc = UPDDocument(
                document_number=doc_number,
                document_date=doc_date,
                supplier_name=supplier_name,
                supplier_inn=supplier_inn,
                items=items,
                total_without_vat=total_without_vat,
                total_vat=total_vat,
                total_with_vat=total_with_vat,
                item_count=len(items),
                xml_version=xml_version,
                generator=generator,
                parsing_status="SUCCESS" if len(self.parsing_issues) == 0 else f"SUCCESS_WITH_{len(self.parsing_issues)}_ISSUES",
                parsing_issues=self.parsing_issues if self.parsing_issues else None
            )
            
            self.result = doc
            return doc
            
        except Exception as e:
            import traceback
            self.add_issue('error', 'parse', str(e))
            return UPDDocument(
                document_number="UNKNOWN",
                document_date="",
                supplier_name="",
                supplier_inn="",
                items=[],
                total_without_vat=0.0,
                total_vat=0.0,
                total_with_vat=0.0,
                item_count=0,
                xml_version="",
                generator="",
                parsing_status=f"ERROR: {str(e)}",
                parsing_issues=self.parsing_issues if self.parsing_issues else None
            )
    
    def _detect_generator(self, root) -> str:
        """Определяет генератор"""
        # Ищем в ВерсПрог атрибуте
        prog = root.get('ВерсПрог', '')
        if prog:
            return prog
        # Fallback
        prog = root.get('ПрограммаИсточник', '')
        if 'Elewise' in prog or 'LegalDoc' in prog:
            return "Elewise LegalDoc"
        return prog or "Unknown"
    
    def _extract_supplier(self, doc_elem, generator: str = '') -> tuple:
        """Извлекает информацию о поставщике"""
        import re
        
        supplier_name = 'UNKNOWN'
        supplier_inn = ''
        
        # Вариант 1: прямо в атрибуте Документа
        supplier_name = doc_elem.get('НаимЭконСубСост', 'UNKNOWN')
        
        # Из этого строки формата "Компания ИНН / КПП" или "Компания, ИНН/КПП" извлекаем ИНН
        if supplier_name != 'UNKNOWN':
            # Если есть запятая - это формат 1С (e.g. 'ООО "ТЕХНОРЕНТ", ИНН/КПП ...')
            if ',' in supplier_name:
                # Ищем ИНН через регекс в исходной строке
                match = re.search(r'ИНН/?(?:КПП)?\s*(\d{10})', supplier_name)
                if match:
                    supplier_inn = match.group(1)
                else:
                    self.add_issue('warning', 'Лицо (Продавец)', 
                                 f'ИНН не найден в строке: {supplier_name}', generator, supplier_name)
                # Обрезаем всё после запятой
                supplier_name = supplier_name.split(',')[0].strip()
            elif '/' in supplier_name:
                # Стандартный формат с "/" (e.g. 'ООО "ЭНЕРГОКОМ" 7705892151 / 231243001')
                parts = supplier_name.split('/')
                if len(parts) >= 1:
                    # Вторая часть - это КПП
                    left_part = parts[0].strip()
                    # Ищем ИНН в левой части (последние 10 символов перед пробелом)
                    words = left_part.split()
                    for word in reversed(words):
                        if word.isdigit() and len(word) == 10:
                            supplier_inn = word
                            break
                    
                    # Очищаем имя от ИНН
                    supplier_name = left_part.replace(supplier_inn, '').strip()
            else:
                # Может быть только имя без ИНН
                self.add_issue('info', 'Лицо (Продавец)', 
                             'ИНН не найден в имени поставщика', generator)
        
        # Сокращаем название организации
        supplier_name = shorten_org_name(supplier_name)
        
        # Вариант 2: если не нашли в атрибуте, ищем в элементах
        if supplier_name == 'UNKNOWN':
            seller = doc_elem.find('.//Продавец/Лицо')
            if seller is None:
                seller = doc_elem.find('.//Грузоотправитель/Лицо')
            
            if seller is not None:
                name_elem = seller.find('НаимЮЛ')
                if name_elem is not None and name_elem.text:
                    supplier_name = name_elem.text
                else:
                    supplier_name = seller.get('НаимЮЛ', 'UNKNOWN')
                
                # Сокращаем название организации
                supplier_name = shorten_org_name(supplier_name)
                supplier_inn = seller.get('ИНН', '')
        
        return supplier_name, supplier_inn
    
    def _extract_items(self, doc_elem, generator: str = '') -> List[UPDItem]:
        """Извлекает товарные позиции"""
        items = []
        
        # Найти таблицу
        tabl = doc_elem.find('ТаблСчФакт')
        if tabl is None:
            tabl = doc_elem.find('.//ТаблСчФакт')
        
        if tabl is None:
            self.add_issue('warning', 'ТаблСчФакт', 'Таблица товаров не найдена', generator)
            return items
        
        # Ищем все элементы в таблице которые начинаются со "Свед"
        element_count = 0
        for sved_elem in tabl:
            if 'Свед' in sved_elem.tag:
                element_count += 1
                # Пытаемся сначала как услугу (новый формат)
                item = self._parse_sved_tov_usl_sch(sved_elem, generator)
                
                # Если не удалось, пытаемся как обычный товар (старый формат)
                if not item:
                    item = self._parse_sved_tov(sved_elem, generator)
                
                if item:
                    items.append(item)
                else:
                    self.add_issue('warning', sved_elem.tag, 
                                 f'Не удалось распарсить элемент', generator)
        
        if element_count == 0:
            self.add_issue('warning', 'СведТов', 'Позиции товаров не найдены в таблице', generator)
        
        return items
    
    def _parse_sved_tov_usl_sch(self, sved_elem, generator: str = '') -> Optional[UPDItem]:
        """Парсит позицию товара/услуги из СведТовУслСч (версия с вложенной структурой)"""
        try:
            # Название товара - из атрибута Описание
            product_name = sved_elem.get('Описание')
            
            # Сумма без НДС - из атрибута Сумма
            sum_without_vat_str = sved_elem.get('Сумма')
            
            # Если оба атрибута не найдены - это не услуга/товар в этом формате
            if not product_name or not sum_without_vat_str:
                return None
            
            sum_without_vat = float(sum_without_vat_str or 0)
            
            # НДС ставка - из атрибута НДС (формат "20%")
            vat_rate_str = sved_elem.get('НДС', '20%')
            vat_rate = float(vat_rate_str.rstrip('%') if vat_rate_str else '20')
            
            # НДС сумма
            sum_with_vat = float(sved_elem.get('СуммаНДС', 0) or 0)
            vat_amount = sum_with_vat - sum_without_vat if sum_with_vat > 0 else (sum_without_vat * vat_rate / 100)
            
            # Для услуг обычно нет явного кол-во и цены, так что берем 1 с полной ценой
            quantity = 1
            unit = 'услуга'
            unit_price = sum_without_vat
            
            return UPDItem(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                sum_without_vat=sum_without_vat,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
            )
        except Exception as e:
            self.add_issue('error', sved_elem.tag, f'Ошибка парсинга: {str(e)}', generator)
            return None
    
    def _parse_sved_tov(self, sved_elem, generator: str = '') -> Optional[UPDItem]:
        """Парсит одну позицию товара из СведТов"""
        try:
            # Название товара
            product_name = sved_elem.get('НаимТов', 'UNKNOWN')
            
            # Количество
            quantity = float(sved_elem.get('КолТов', 0) or 0)
            
            # Единица (преобразуем код ОКЕИ в нормальное название)
            okei_code = sved_elem.get('ОКЕИ_Тов', '')
            unit = convert_okei_to_unit(okei_code)
            
            # Цена
            unit_price = float(sved_elem.get('ЦенаТов', 0) or 0)
            
            # Сумма без НДС
            sum_without_vat = float(sved_elem.get('СтТовБезНДС', 0) or 0)
            
            # НДС ставка (может быть в НалСт или НДС)
            vat_rate_str = sved_elem.get('НалСт') or sved_elem.get('НДС') or '20%'
            vat_rate = float(vat_rate_str.rstrip('%') if vat_rate_str else '20')
            
            # НДС сумма (вычисляем или берем из СтТовУчНал - СтТовБезНДС)
            sum_with_vat = float(sved_elem.get('СтТовУчНал', 0) or 0)
            vat_amount = sum_with_vat - sum_without_vat
            
            # Если нет кол-во и цены (это услуга без явной цены/кол-во)
            if quantity == 0 and unit_price == 0 and sum_without_vat > 0:
                quantity = 1
                unit_price = sum_without_vat
                if not unit or unit == '':
                    unit = 'услуга'
                self.add_issue('info', sved_elem.tag, 
                             'Обнаружена услуга без явной цены/кол-во, установлено qty=1', generator)
            
            return UPDItem(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                sum_without_vat=sum_without_vat,
                vat_rate=vat_rate,
                vat_amount=vat_amount
            )
        except Exception as e:
            self.add_issue('error', sved_elem.tag, f'Ошибка парсинга: {str(e)}', generator)
            return None
    
    def _extract_totals(self, doc_elem) -> tuple:
        """Извлекает итоги"""
        total_without_vat = 0.0
        total_vat = 0.0
        total_with_vat = 0.0
        
        tabl = doc_elem.find('ТаблСчФакт')
        if tabl is None:
            tabl = doc_elem.find('.//ТаблСчФакт')
        
        if tabl is None:
            return total_without_vat, total_vat, total_with_vat
        
        # Итоги находятся в ВсегоОпл (основное место)
        itog = tabl.find('ВсегоОпл')
        
        if itog is not None:
            total_without_vat = float(itog.get('СтТовБезНДСВсего', 0) or 0)
            total_with_vat = float(itog.get('СтТовУчНалВсего', 0) or 0)
            total_vat = total_with_vat - total_without_vat
        
        return total_without_vat, total_vat, total_with_vat


def parse_all_upd_files(directory: str) -> List[tuple]:
    """Парсит все XML файлы в директории"""
    results = []
    xml_files = list(Path(directory).glob('*.xml'))
    
    for xml_file in sorted(xml_files):
        parser = UPDParser(str(xml_file))
        doc = parser.parse()
        results.append((xml_file.name, doc))
    
    return results


if __name__ == '__main__':
    test_file = r'c:\Users\milena\Desktop\new 2\ON_NSCHFDOPPR_2BE4af7d492f0cd40b8b23f4d4cdf5917b4_2BM-7705892151-2013022109563294037440000000000_20240706_AEDCEFE7-D4B5-44DB-AA57-2314A5BF4A77.xml'
    
    parser = UPDParser(test_file)
    doc = parser.parse()
    
    print(f"Status: {doc.parsing_status}")
    print(f"Document: {doc.document_number} ({doc.document_date})")
    print(f"Supplier: {doc.supplier_name} (ИНН: {doc.supplier_inn})")
    print(f"Generator: {doc.generator}, Version: {doc.xml_version}")
    print(f"Items: {doc.item_count}")
    print(f"Total: {doc.total_with_vat} руб (НДС: {doc.total_vat} руб)")
    print(f"\nFirst 3 items:")
    for item in doc.items[:3]:
        print(f"  - {item.product_name}: {item.quantity} {item.unit} @ {item.unit_price} = {item.sum_without_vat} (НДС: {item.vat_amount})")
