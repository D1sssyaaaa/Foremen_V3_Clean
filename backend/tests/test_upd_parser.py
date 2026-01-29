"""Тесты для парсера УПД"""
import pytest
from decimal import Decimal
from app.upd.upd_parser import UPDParser, UPDParseError


def test_parse_valid_upd(sample_upd_xml):
    """Тест парсинга валидного УПД"""
    parser = UPDParser()
    data = parser.parse(sample_upd_xml.encode('windows-1251'))
    
    assert data.document_number == '123'
    assert data.document_date == '01.01.2024'
    assert data.supplier_name == 'ООО Поставщик'
    assert data.supplier_inn == '1234567890'
    assert len(data.items) == 1
    
    item = data.items[0]
    assert item.product_name == 'Цемент М500'
    assert item.quantity == Decimal('100')
    assert item.unit == 'шт'
    assert item.price == Decimal('500')
    assert item.amount == Decimal('50000')
    assert item['vat_rate'] == '20%'


def test_parse_upd_with_services():
    """Тест парсинга УПД с услугами (без количества)"""
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт НомерСчФ="456" ДатаСчФ="15.02.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Услуги" ИННЮЛ="9876543210"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Консультационные услуги" СтТовБезНДС="100000">
            <НалСт>20%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
    
    parser = UPDParser()
    data = parser.parse(xml.encode('windows-1251'))
    
    assert data['document_number'] == '456'
    assert len(data['items']) == 1
    
    item = data['items'][0]
    assert item['product_name'] == 'Консультационные услуги'
    assert item['quantity'] == Decimal('1')  # Услуга - количество 1
    assert item['unit'] == 'услуга'
    assert item['price'] == Decimal('100000')
    assert item['amount'] == Decimal('100000')


def test_parse_upd_with_0_vat():
    """Тест парсинга УПД с НДС 0%"""
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт НомерСчФ="789" ДатаСчФ="20.03.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Экспорт" ИННЮЛ="1111111111"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Товар на экспорт" КолТов="50" ОКЕИ_Тов="796" ЦенаТов="1000" СтТовБезНДС="50000">
            <НалСт>0%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
    
    parser = UPDParser()
    data = parser.parse(xml.encode('windows-1251'))
    
    item = data['items'][0]
    assert item['vat_rate'] == '0%'


def test_parse_upd_invalid_xml():
    """Тест парсинга невалидного XML"""
    invalid_xml = "<invalid>test</invalid>"
    
    with pytest.raises(UPDParseError):
        parser = UPDParser()
        parser.parse(invalid_xml.encode('windows-1251'))


def test_parse_upd_missing_required_fields():
    """Тест парсинга УПД без обязательных полей"""
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт>
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Test"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
</Файл>'''
    
    with pytest.raises(UPDParseError):
        parser = UPDParser(xml)
        parser.parse()


def test_parse_upd_with_different_generator():
    """Тест парсинга УПД от разных генераторов"""
    # УПД от 1С
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Генератор="1С:Бухгалтерия 8">
    <СвСчФакт НомерСчФ="1C-001" ДатаСчФ="10.04.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Ромашка, ИНН/КПП 1234567890/123456789" ИННЮЛ="1234567890"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Песок речной" КолТов="20" ОКЕИ_Тов="113" ЦенаТов="300" СтТовБезНДС="6000">
            <НалСт>20%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
    
    parser = UPDParser()
    data = parser.parse(xml.encode('windows-1251'))
    
    # Проверить что имя поставщика очищено от ИНН/КПП
    assert 'ИНН/КПП' not in data['supplier_name']
    assert data['supplier_name'] == 'ООО Ромашка'
    assert data['supplier_inn'] == '1234567890'


def test_okei_code_mapping():
    """Тест маппинга кодов ОКЕИ в единицы измерения"""
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт НомерСчФ="OK-001" ДатаСчФ="01.05.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Test" ИННЮЛ="1111111111"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Аренда техники" КолТов="24" ОКЕИ_Тов="356" ЦенаТов="500" СтТовБезНДС="12000">
            <НалСт>20%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
    
    parser = UPDParser()
    data = parser.parse(xml.encode('windows-1251'))
    
    item = data['items'][0]
    assert item['unit'] == 'ч'  # Код 356 = часы


def test_parsing_issues_tracking():
    """Тест что проблемы парсинга фиксируются"""
    xml = '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт НомерСчФ="WARN-001" ДатаСчФ="01.06.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Test" ИННЮЛ="1111111111"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Товар с неизвестным ОКЕИ" КолТов="10" ОКЕИ_Тов="999" ЦенаТов="100" СтТовБезНДС="1000">
            <НалСт>20%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
    
    parser = UPDParser()
    data = parser.parse(xml.encode('windows-1251'))
    
    # Должна быть хотя бы одна проблема (неизвестный код ОКЕИ)
    assert 'parsing_issues' in data
    assert len(data['parsing_issues']) > 0
    
    # Проверить что единица измерения вернулась как код
    item = data['items'][0]
    assert item['unit'] == '999'
