"""Database initialization entry point.

Usage:
    python -m frc_data_281.db
"""
from frc_data_281.db.schema import create_schema

if __name__ == "__main__":
    print("Initializing scouting database schema...")
    create_schema()
    print("✓ Database schema initialized successfully")
    print("  - scouting.pit")
    print("  - scouting.tags")
    print("  - scouting.test")
