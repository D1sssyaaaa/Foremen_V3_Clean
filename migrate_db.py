import sqlite3
import os

DB_PATH = "backend/construction_costs.db"

print(f"Checking for DB at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("DB not found!")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(cost_objects)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'customer_name' not in columns:
        print("Adding customer_name column...")
        cursor.execute("ALTER TABLE cost_objects ADD COLUMN customer_name VARCHAR(255)")
        conn.commit()
        print("Migration successful.")
    else:
        print("Column customer_name already exists.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
