import duckdb
import polars as pl

DB_PATH = "db/frc2026.duckdb"

con = duckdb.connect(DB_PATH)


def get_connection():
    """Return the shared database connection."""
    return con
