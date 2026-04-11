"""Database schema creation and management.

This module contains the code to create schema objects,
if we have manually created tables.
"""
from frc_data_281.db.connection import get_connection


def create_schema():
    with get_connection() as con:
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
            CREATE TABLE IF NOT EXISTS scouting.tags (
                id BIGINT,
                event_key VARCHAR NOT NULL,
                team_number INTEGER NOT NULL,
                tag VARCHAR NOT NULL,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_key, team_number, tag),
                UNIQUE(id)
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
                drive_type VARCHAR,
                auto_route BLOB,
                robot_photo BLOB,
                scoring_capabilities VARCHAR,
                preferred_scoring VARCHAR,
                notes TEXT,
                author VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Note: scoring_capabilities and preferred_scoring are comma-separated lists
        # with values from: "Touching Hub", "Mid Range", "Long shot", "Trench shot",
        # "L1 Climb", "L2 Climb", "L3 Climb", "Snowblow"
        # drive_type options: "Mecanum", "Tank", "Swerve", "H Drive", "Other"

        con.sql("""
            CREATE TABLE IF NOT EXISTS scouting.match_data (
                record_id INTEGER,
                event_key VARCHAR NOT NULL,
                match_number INTEGER NOT NULL,
                team_number INTEGER NOT NULL,
                auto_fuel_score INTEGER,
                auto_climb_try BOOLEAN,
                auto_climbed VARCHAR,
                auto_traveled VARCHAR,
                teleop_fuel_score INTEGER,
                teleop_traveled VARCHAR,
                endgame_climb_try BOOLEAN,
                endgame_climb_level VARCHAR,
                strategy_active_scored BOOLEAN,
                strategy_active_ferrying BOOLEAN,
                strategy_active_defense BOOLEAN,
                strategy_inactive_scored BOOLEAN,
                strategy_inactive_ferrying BOOLEAN,
                strategy_inactive_defense BOOLEAN,
                strategy_defense_actions INTEGER,
                match_fouls INTEGER,
                match_tipped BOOLEAN,
                match_broken BOOLEAN,
                match_beached BOOLEAN,
                match_carded BOOLEAN,
                match_disabled BOOLEAN,
                match_absent BOOLEAN,
                alliance_human_fuel INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_key, match_number, team_number)
            );
        """)
