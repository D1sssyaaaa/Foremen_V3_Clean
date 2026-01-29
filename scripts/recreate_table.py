
import sqlite3
import os
import time

# Путь к БД: backend/app.db
# Скрипт лежит в scripts/, значит ../backend/app.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "construction_costs.db")

def recreate_table():
    print(f"Connecting to {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🗑️ Удаление старой таблицы upd_distribution...")
        cursor.execute("DROP TABLE IF EXISTS upd_distribution")

        print("🏗️ Создание новой таблицы...")
        sql = """
        CREATE TABLE upd_distribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_cost_id INTEGER NOT NULL,
            material_cost_item_id INTEGER NOT NULL,
            material_request_id INTEGER,
            cost_object_id INTEGER,
            distributed_quantity FLOAT NOT NULL,
            distributed_amount FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_cost_id) REFERENCES material_costs (id) ON DELETE CASCADE,
            FOREIGN KEY (material_cost_item_id) REFERENCES material_cost_items (id) ON DELETE CASCADE,
            FOREIGN KEY (material_request_id) REFERENCES material_requests (id) ON DELETE CASCADE,
            FOREIGN KEY (cost_object_id) REFERENCES cost_objects (id) ON DELETE CASCADE
        );
        """
        cursor.execute(sql)
        cursor.execute("CREATE INDEX ix_upd_distribution_id ON upd_distribution (id)")
        
        conn.commit()
        print("✅ Таблица успешно пересоздана.")
        conn.close()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("❌ База данных заблокирована. Пожалуйста, остановите сервер backend.")
        else:
            print(f"❌ Ошибка SQLite: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    recreate_table()
