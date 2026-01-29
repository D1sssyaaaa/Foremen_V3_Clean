"""Скрипт для исправления тестов УПД"""
import re
import os

os.chdir(r'c:\Users\milena\Desktop\new 2')

# Читаем файл
with open('backend/tests/test_upd_parser.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Паттерн для замены
pattern = r'parser = UPDParser\(xml\)\s*data = parser\.parse\(\)'
replacement = 'parser = UPDParser()\n    data = parser.parse(xml.encode(\'windows-1251\'))'

# Заменяем
content = re.sub(pattern, replacement, content)

# Также заменяем паттерн с invalid_xml
pattern2 = r'parser = UPDParser\(invalid_xml\)\s*parser\.parse\(\)'
replacement2 = 'parser = UPDParser()\n        parser.parse(invalid_xml.encode(\'windows-1251\'))'
content = re.sub(pattern2, replacement2, content)

# Сохраняем
with open('backend/tests/test_upd_parser.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Тесты исправлены")
