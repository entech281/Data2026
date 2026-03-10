import duckdb
conn = duckdb.connect('data/frc2026.duckdb')

# List all tables
print("All tables in database:")
tables = conn.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name
""").fetchall()

if tables:
    for schema, table in tables:
        print(f"  {schema}.{table}")
else:
    print("  (no tables found)")

# Count rows in each table
print("\nRow counts:")
for schema, table in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
    print(f"  {schema}.{table}: {count} rows")

conn.close()

