import duckdb
import polars as pl
import streamlit as st

ACCESS_TOKEN=st.secrets['motherduck']['token']
con = duckdb.connect(f"md:frc_2025?motherduck_token={ACCESS_TOKEN}")

def copy_db_to_local():

    EXPORT_PATH="./data/frc2025_export"
    con.execute(f"EXPORT DATABASE  '{EXPORT_PATH}' ")
    local_con = duckdb.connect("data/frc2025_copy.duckdb")
    local_con.execute(f"IMPORT DATABASE '{EXPORT_PATH}'")

    #local_con.close()
    con.close()


if __name__ == '__main__':
    copy_db_to_local()