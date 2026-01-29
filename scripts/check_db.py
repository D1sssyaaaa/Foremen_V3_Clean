
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "construction_costs.db")

def check_db():
    print(f"Connecting to {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("❌ Файл БД не найден!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(upd_distribution)")
        columns = cursor.fetchall()
        print("Columns in upd_distribution:")
        found = False
        for col in columns:
            print(col)
            if col[1] == 'material_cost_item_id':
                found = True
        
        if found:
            print("✅ Колонка material_cost_item_id найдена.")
        else:
            print("❌ Колонка material_cost_item_id НЕ найдена.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db()
