import pytest
from httpx import AsyncClient
import xml.etree.ElementTree as ET
import os

@pytest.mark.asyncio
async def test_xxe_injection(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: XXE Injection
    Try to read /etc/passwd (or C:/Windows/win.ini) using an external entity.
    """
    xxe_payload = """<?xml version="1.0" encoding="windows-1251"?>
    <!DOCTYPE foo [
      <!ELEMENT foo ANY >
      <!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini" >]>
    <Файл>
        <Документ НомерДокумента="XXE-TEST" ДатаДокумента="2025-01-01">
            <Таблица>
                <Товар НаимТов="&xxe;" КолТов="1" ЦенаТов="100" СтТовБезНДС="100" СтавкаНДС="20" СумНДС="20" СуммаВсего="120" ЕдИзм="шт" />
            </Таблица>
            <ИтогДокумента ДокСумма="100" СумНДС="20" СуммаВсего="120" />
        </Документ>
    </Файл>
    """
    
    # Save payload to a file (optional, but good for debugging)
    
    token = mock_roles("ACCOUNTANT")
    files = {"file": ("xxe.xml", xxe_payload.encode('windows-1251'), "text/xml")}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.post("/api/v1/material-costs/upload", files=files, headers=headers)
    
    # The parser SHOULD fail or NOT return the content of win.ini
    # If it returns 201 Created and the product name contains "[extensions]", we are vulnerable.
    
    print(f"XXE Response: {response.text}")
    assert response.status_code in [400, 201]
    
    if response.status_code == 201:
        data = response.json()
        # Verify that the parsed product name is NOT the content of the file
        item_name = data['items'][0]['product_name']
        assert "[extensions]" not in item_name, "VULNERABILITY CONFIRMED: XXE successfully read local file!"
        assert "font" not in item_name.lower(), "Warning: Possible XXE leak detected."

@pytest.mark.asyncio
async def test_billion_laughs_attack(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Billion Laughs (XML Bomb)
    Nested entities expanding exponentially.
    """
    billion_laughs = """<?xml version="1.0"?>
    <!DOCTYPE lolz [
     <!ENTITY lol "lol">
     <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
     <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
     <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
     <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
     <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
     <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
     <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
     <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
     <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
    ]>
    <Файл>
        <Документ НомерДокумента="BOMB" ДатаДокумента="2025-01-01">
            <Таблица>
                <Товар НаимТов="&lol9;" КолТов="1" ЦенаТов="100" СтТовБезНДС="100" СтавкаНДС="20" СумНДС="20" СуммаВсего="120" ЕдИзм="шт" />
            </Таблица>
        </Документ>
    </Файл>
    """
    
    token = mock_roles("ACCOUNTANT")
    files = {"file": ("bomb.xml", billion_laughs.encode('utf-8'), "text/xml")}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Set a timeout. If it takes > 2 seconds, it's likely vulnerable to DoS.
        response = await async_client.post("/api/v1/material-costs/upload", files=files, headers=headers, timeout=5.0)
        print(f"Bomb Response: {response.status_code}")
        # Ideally, it should be rejected or handled safely.
        # Python's xml.etree is vulnerable to billionaire laughs if not configured securely (defusedxml is recommended).
    except Exception as e:
        pytest.fail(f"Parser crashed/timed out on Billion Laughs attack: {e}")

@pytest.mark.asyncio
async def test_encoding_mismatch_attack(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Encoding Mismatch
    The spec requires windows-1251. We feed UTF-8 with BOM and valid 1251 characters mixed.
    """
    # Create content that is valid UTF-8 but interprets differently in 1251
    # Or just a simple UTF-8 file.
    utf8_payload = """<?xml version="1.0" encoding="utf-8"?>
    <Файл>
        <Документ НомерДокумента="UTF8-TEST" ДатаДокумента="2025-01-01">
            <Таблица>
                <Товар НаимТов="Тест 🧪" КолТов="1" ЦенаТов="100" СтТовБезНДС="100" СтавкаНДС="20" СумНДС="20" СуммаВсего="120" ЕдИзм="шт" />
            </Таблица>
             <ИтогДокумента ДокСумма="100" СумНДС="20" СуммаВсего="120" />
        </Документ>
    </Файл>
    """
    
    token = mock_roles("ACCOUNTANT")
    files = {"file": ("utf8.xml", utf8_payload.encode('utf-8'), "text/xml")} # Sent as bytes
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.post("/api/v1/material-costs/upload", files=files, headers=headers)
    
    # Expect 400 Bad Request (Encoding Error) or successful handling if auto-detection works.
    print(f"Encoding Response: {response.text}")
    assert response.status_code == 400 or response.status_code == 201

@pytest.mark.asyncio
async def test_logic_bomb_prices(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Logic Bomb
    Price = 0, Quantity = 1, but Total = 1,000,000.
    Does the system accept this mismatch?
    """
    payload = """<?xml version="1.0" encoding="windows-1251"?>
    <Файл>
        <Документ НомерДокумента="LOGIC-BOMB" ДатаДокумента="2025-01-01">
            <Таблица>
                <Товар НаимТов="Fake Gold" КолТов="1" ЦенаТов="0" СтТовБезНДС="1000000" СтавкаНДС="0" СумНДС="0" СуммаВсего="1000000" ЕдИзм="шт" />
            </Таблица>
            <ИтогДокумента ДокСумма="1000000" СумНДС="0" СуммаВсего="1000000" />
        </Документ>
    </Файл>
    """
    
    token = mock_roles("ACCOUNTANT")
    files = {"file": ("logic.xml", payload.encode('windows-1251'), "text/xml")}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.post("/api/v1/material-costs/upload", files=files, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    item = data['items'][0]
    
    # Check if the system sanitized the values or accepted them as is
    # A robust system might flag this.
    assert item['amount'] == 1000000
    assert item['price'] == 0
    # Ideally, there should be a warning in parsing_issues
    assert len(data['parsing_issues']) > 0 or "Logic check failed" in response.text
