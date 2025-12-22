# this contains the code to create schmea objects,
# if we have manually created tables
from motherduck import con



def create_schema():
    con.sql("""
        create or replace table scouting.test (
            id INTEGER PRIMARY KEY,
            foo varchar,
            bar varchar,
            mod_dte timestamp default current_timestamp
        );
    """)

    con.sql("""
        create or replace table scouting.tags (
            team_number INTEGER PRIMARY KEY,
            tag varchar,
             mod_dte timestamp default current_timestamp
        );
    """)

    con.sql("""
        CREATE OR REPLACE TABLE scouting.pit (
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