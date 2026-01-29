import sqlite3

conn = sqlite3.connect('construction_costs.db')
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = cur.fetchall()

print("\n=== Таблицы в БД ===")
for table in tables:
    print(f"  ✓ {table[0]}")
    
conn.close()
print(f"\nВсего таблиц: {len(tables)}")
