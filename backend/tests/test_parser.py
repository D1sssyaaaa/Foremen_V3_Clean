"""Тест парсера Excel табелей"""
import sys
sys.path.append('C:\\Users\\milena\\Desktop\\new 2\\backend')

from app.time_sheets.excel_parser import TimeSheetExcelParser, TimeSheetExcelParseError

def test_parser():
    """Тестирование парсера"""
    try:
        parser = TimeSheetExcelParser("test_timesheet.xlsx")
        data = parser.parse()
        
        print("=" * 60)
        print("РЕЗУЛЬТАТЫ ПАРСИНГА ТАБЕЛЯ")
        print("=" * 60)
        
        print(f"\nБригада: {data['brigade_name']}")
        print(f"Период: {data['period_start']} - {data['period_end']}")
        print(f"Количество записей: {len(data['items'])}\n")
        
        print("Первые 3 записи:")
        print("-" * 60)
        for i, item in enumerate(data['items'][:3], 1):
            print(f"{i}. {item['member_name']}")
            print(f"   Дата: {item['date']}, Объект: {item['cost_object_name']}")
            print(f"   Часы: {item['hours']}")
        
        if len(data['items']) > 3:
            print(f"\n... и еще {len(data['items']) - 3} записей")
        
        print("\n" + "=" * 60)
        print("✓ ПАРСИНГ УСПЕШЕН")
        print("=" * 60)
        
    except TimeSheetExcelParseError as e:
        print(f"\n✗ ОШИБКА ПАРСИНГА: {e}")
    except Exception as e:
        print(f"\n✗ НЕОЖИДАННАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_parser()
