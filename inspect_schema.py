import duckdb

print("=" * 60)
print("2025 SCHEMA (from duckdb)")
print("=" * 60)
conn = duckdb.connect('data/frc2025.duckdb')
tables = conn.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE' ORDER BY table_schema, table_name").fetchall()

for schema, table in tables:
    print(f"\n{schema}.{table}")
    cols = conn.execute(f"DESCRIBE {schema}.{table}").fetchall()
    for col in cols:
        print(f"  {col[0]}: {col[1]}")

print("\n" + "=" * 60)
print("2026 SCHEMA (from setup_db.py)")
print("=" * 60)
conn2 = duckdb.connect('frc2026.duckdb')
tables2 = conn2.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE' ORDER BY table_schema, table_name").fetchall()

for schema, table in tables2:
    print(f"\n{schema}.{table}")
    cols = conn2.execute(f"DESCRIBE {schema}.{table}").fetchall()
    for col in cols:
        print(f"  {col[0]}: {col[1]}")
