import xml.etree.ElementTree as ET

with open(r'c:\Users\milena\Desktop\new 2\ON_NSCHFDOPPR_2BE4af7d492f0cd40b8b23f4d4cdf5917b4_2BM-7705892151-2013022109563294037440000000000_20240706_AEDCEFE7-D4B5-44DB-AA57-2314A5BF4A77.xml', 'r', encoding='windows-1251') as f:
    content = f.read()
    root = ET.fromstring(content)

# Найдем Лицо со странным номером
doc = root.find('.//Документ')
print("Searching for supplier...")

for elem in doc.iter():
    if elem.tag == 'Лицо' or 'Лицо' in elem.tag:
        name = elem.get('НаимЮЛ', 'NOPE')
        inn = elem.get('ИНН', 'NOPE')
        if 'энергоком' in name.lower() or '7705892151' in inn:
            print(f"Found Licо: {elem.tag}")
            print(f"  НаимЮЛ: {name}")
            print(f"  ИНН: {inn}")
            print(f"  Родитель: {[p.tag for p in doc.iter() if elem in list(p)]}")

# Поищем атрибут в СчФактура (может быть как атрибут СчФактуры)
print("\nLooking for НаимЭконСубСост in root Документ:")
print(f"Root doc.attrib: {root.find('.//Документ').attrib.get('НаимЭконСубСост', 'NOT FOUND')}")

# Напрямую ищем строку компании
print("\nSearching in raw content:")
if 'ЭНЕРГОКОМ' in content:
    print("Found ЭНЕРГОКОМ in raw XML")


