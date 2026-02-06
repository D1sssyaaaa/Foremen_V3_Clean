import sqlite3
import os

DB_PATH = os.path.join("construction_costs.db")

def migrate():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Adding hour_rate column...")
        cursor.execute("ALTER TABLE time_sheet_items ADD COLUMN hour_rate FLOAT")
        print("Success.")
    except Exception as e:
        print(f"Skipped (maybe exists): {e}")

    try:
        print("Adding amount column...")
        cursor.execute("ALTER TABLE time_sheet_items ADD COLUMN amount FLOAT")
        print("Success.")
    except Exception as e:
        print(f"Skipped (maybe exists): {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
