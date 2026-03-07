"""Database schema creation and management.

This module contains the code to create schema objects,
if we have manually created tables.
"""
from frc_data_281.db.connection import con


def create_schema():
    con.sql("CREATE SCHEMA IF NOT EXISTS scouting")

    con.sql("""
        create table if not exists scouting.test (
            id INTEGER PRIMARY KEY,
            foo varchar,
            bar varchar,
            mod_dte timestamp default current_timestamp
        );
    """)

    con.sql("""
        create table if not exists scouting.tags (
            team_number INTEGER PRIMARY KEY,
            tag varchar,
             mod_dte timestamp default current_timestamp
        );
    """)

    con.sql("""
        CREATE TABLE IF NOT EXISTS scouting.pit (
            team_number INTEGER,
            height INTEGER,
            weight INTEGER,
            length INTEGER,
            width INTEGER,
            start_position VARCHAR,
            auto_route BLOB,
            scoring_capabilities VARCHAR,
            preferred_scoring VARCHAR,
            notes TEXT,
            author VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
