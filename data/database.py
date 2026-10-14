# data/database.py
# SQLite database manager
# Zero setup, portable, perfect for portfolio

import sqlite3
import pandas as pd
import os
import uuid
import gc
import time
from pathlib import Path

DB_FOLDER = Path("data/sessions")
DB_FOLDER.mkdir(parents=True, exist_ok=True)


class DatabaseManager:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.db_path = (
            DB_FOLDER / f"session_{self.session_id}.db"
        )
        self.table_name = "user_data"
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        return self.connection

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def load_dataframe(self, df: pd.DataFrame) -> bool:
        try:
            conn = self.connect()
            df.to_sql(
                name=self.table_name,
                con=conn,
                if_exists='replace',
                index=False,
                chunksize=1000
            )
            cursor = conn.cursor()
            for col in df.columns[:3]:
                safe_col = col.replace(
                    ' ', '_').replace('-', '_')
                try:
                    cursor.execute(
                        f"CREATE INDEX IF NOT EXISTS "
                        f"idx_{safe_col} "
                        f"ON {self.table_name}({col})"
                    )
                except Exception:
                    pass
            conn.commit()
            print(
                f"✅ Loaded: {len(df)} rows, "
                f"{len(df.columns)} cols"
            )
            return True
        except Exception as e:
            print(f"❌ Load error: {e}")
            return False

    def execute_query(self, sql: str) -> pd.DataFrame:
        try:
            conn = self.connect()
            return pd.read_sql_query(sql, conn)
        except Exception as e:
            raise Exception(f"Query error: {str(e)}")

    def get_schema(self) -> str:
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                f"PRAGMA table_info({self.table_name})"
            )
            columns = cursor.fetchall()
            cursor.execute(
                f"SELECT COUNT(*) FROM {self.table_name}"
            )
            row_count = cursor.fetchone()[0]
            cursor.execute(
                f"SELECT * FROM {self.table_name} LIMIT 3"
            )
            sample = cursor.fetchall()

            schema = f"Table: {self.table_name}\n"
            schema += f"Total rows: {row_count}\n"
            schema += "Columns:\n"
            for col in columns:
                schema += f"  - {col[1]} ({col[2]})\n"
            schema += "\nSample (first 3 rows):\n"
            for row in sample:
                schema += f"  {row}\n"
            return schema
        except Exception as e:
            return f"Schema error: {str(e)}"

    def get_column_stats(self) -> dict:
        try:
            conn = self.connect()
            df = pd.read_sql_query(
                f"SELECT * FROM {self.table_name} "
                f"LIMIT 1000",
                conn
            )
            return {
                col: {
                    'dtype': str(df[col].dtype),
                    'null_count': int(
                        df[col].isnull().sum()),
                    'unique_count': int(df[col].nunique())
                } for col in df.columns
            }
        except Exception:
            return {}

    def cleanup(self):
        """Delete session database file safely"""
        try:
            self.disconnect()
            gc.collect()
            time.sleep(0.1)
            if self.db_path.exists():
                os.remove(self.db_path)
                print("🗑️ Session cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


def get_db(session_id: str = None) -> DatabaseManager:
    return DatabaseManager(session_id)