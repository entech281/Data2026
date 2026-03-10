import duckdb
import polars as pl
from contextlib import contextmanager
import os

DB_PATH = "db/frc2026.duckdb"


@contextmanager
def get_connection():
    """Context manager for database connections.
    
    Opens a connection only when needed and closes it after use.
    Prevents long-lived locks on the database file.
    
    Usage:
        with get_connection() as con:
            con.sql("SELECT ...").df()
    """
    # Ensure db directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = duckdb.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
