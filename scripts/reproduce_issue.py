
import sys
import os
# Добавляем backend в путь импорта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.upd.upd_parser import UPDParser
import glob

def main():
    # Ищем XML файлы
    xml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "xml")
    xml_files = glob.glob(os.path.join(xml_dir, "*.xml"))
    
    if not xml_files:
        print("XML files not found")
        return

    file_path = xml_files[0]
    print(f"Testing file: {file_path}")
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    parser = UPDParser()
    try:
        doc = parser.parse(content)
        print(f"Success! Amount: {doc.total_with_vat}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Попытка прочитать XML как текст и показать начало
        try:
             text = content.decode('windows-1251')
             print("\nXML Snippet:")
             print(text[:500])
             
             # Поиск числовых полей
             import re
             print("\nSearching for potential number issues:")
             for match in re.finditer(r'(СумНал|СтТовУчНал|ЦенаТов|КолТов)="([^"]*)"', text):
                 print(f"{match.group(1)}='{match.group(2)}'")
                 # Проверка на пробелы
                 if ' ' in match.group(2):
                     print("  -> WARNING: Spaces detected!")
        except Exception as decode_err:
             print(f"Decode error: {decode_err}")

if __name__ == "__main__":
    main()
