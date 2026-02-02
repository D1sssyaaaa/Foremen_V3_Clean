
import asyncio
import os
import sys
import datetime
from dateutil import parser
from sqlalchemy import create_engine, MetaData, select, insert, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

SQLITE_URL = "sqlite:///./construction_costs.db"
POSTGRES_URL = settings.database_url

async def migrate_data():
    print(f"Migrating from {SQLITE_URL} to {POSTGRES_URL}...")
    
    sqlite_engine = create_engine(SQLITE_URL)
    pg_engine = create_async_engine(POSTGRES_URL)
    
    # 1. Reflect Target (Postgres)
    pg_sync_url = POSTGRES_URL.replace("+asyncpg", "")
    pg_sync_engine = create_engine(pg_sync_url)
    metadata_target = MetaData()
    metadata_target.reflect(bind=pg_sync_engine)
    
    sorted_tables = metadata_target.sorted_tables
    
    # 2. Inspect Source (SQLite)
    inspector = inspect(sqlite_engine)
    source_table_names = set(inspector.get_table_names())
    print(f"Source tables: {source_table_names}")
    
    for target_table in sorted_tables:
        table_name = target_table.name
        if table_name == 'alembic_version':
            continue
        
        print(f"Processing target table: {table_name}")
        
        if table_name not in source_table_names:
            print(f"  Skipping {table_name} (not found in source)")
            continue
            
        try:
            with sqlite_engine.connect() as sqlite_conn:
                result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                
                if not rows:
                    print(f"  No data.")
                    continue
                
                source_cols = result.keys() 
                data = []
                target_col_names = set(c.name for c in target_table.columns)
                target_cols_info = {c.name: c for c in target_table.columns}

                for row in rows:
                    row_dict = dict(zip(source_cols, row))
                    
                    # Filter columns
                    row_dict = {k: v for k, v in row_dict.items() if k in target_col_names}
                    
                    # Validate Not Null constraints (Basic check for FKs logic drift)
                    skip_row = False
                    for col_name, val in row_dict.items():
                        col = target_cols_info.get(col_name)
                        if col is not None and not col.nullable and val is None:
                            # If default exists, maybe ok? But if no default, it will fail.
                            if col.server_default is None and col.default is None:
                                # Special case for upd_distribution material_request_id
                                if table_name == 'upd_distribution' and col_name == 'material_request_id':
                                    skip_row = True
                                    break
                    if skip_row:
                        continue

                    # Fix Types
                    for col_name, val in row_dict.items():
                        col = target_cols_info.get(col_name)
                        if col is not None:
                            col_type = str(col.type).lower()
                            if 'boolean' in col_type and isinstance(val, int):
                                row_dict[col_name] = bool(val)
                            
                            if ('date' in col_type or 'time' in col_type) and isinstance(val, str):
                                try:
                                    dt = parser.parse(val)
                                    if 'date' in col_type and 'time' not in col_type:
                                        row_dict[col_name] = dt.date()
                                    else:
                                        row_dict[col_name] = dt
                                except:
                                    pass
                    
                    data.append(row_dict)
                
                print(f"  Inserting {len(data)} rows...")
                
                if not data:
                    continue

                async with pg_engine.begin() as pg_conn:
                    # Disable Triggers (FK checks)
                    await pg_conn.execute(text(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL;"))
                    
                    chunk_size = 1000
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i+chunk_size]
                        await pg_conn.execute(insert(target_table).values(chunk))
                    
                    await pg_conn.execute(text(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL;"))

                    # Sequences
                    pk_col = None
                    for col in target_table.primary_key:
                        if col.autoincrement:
                            pk_col = col.name
                            break
                    
                    if pk_col:
                         max_id = max([r.get(pk_col, 0) for r in data if isinstance(r.get(pk_col), (int, float))])
                         if max_id > 0:
                             seq_name = f"{table_name}_{pk_col}_seq"
                             try:
                                await pg_conn.execute(text(f"SELECT setval('{seq_name}', {max_id + 1}, false)"))
                             except:
                                pass

        except Exception as e:
            print(f"  Error migrating {table_name}: {e}")
            continue

    print("Migration completed!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate_data())
