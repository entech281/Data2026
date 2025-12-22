import streamlit as st
import pandas as pd
import re
from motherduck import con

st.title("Upload Match CSV Data")

def normalize_column_name(name: str) -> str:
    """
    Normalize a CSV header to a database column name.
    
    This lowercases the string, replaces any non-alphanumeric characters 
    with underscores and strips any leading/trailing underscores.
    
    Parameters:
        name (str): The original column name.
    
    Returns:
        str: Normalized column name.
    """
    # Lowercase the header.
    new_name = name.lower()

    st.write(new_name)
    new_name = new_name.replace("’", "")
    st.write(new_name)
    # Replace non-alphanumeric characters with underscore.
    new_name = re.sub(r"[^a-z0-9]+", "_", new_name)
    # Remove leading/trailing underscores.
    new_name = new_name.strip("_")
    return new_name

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV file into DataFrame
        df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded data (raw headers):")
        st.dataframe(df)
        
        # Normalize column names to match the database schema.
        df.columns = [normalize_column_name(col) for col in df.columns]
        
        st.write("Preview of uploaded data (normalized headers):")
        st.dataframe(df)
        
        # Confirm before upload
        if st.button("Upload to Database"):
            # Build dynamic SQL query based on normalized column names.
            columns = df.columns.tolist()
            col_str = ", ".join(columns)
            placeholders = ", ".join(["?"] * len(columns))
            sql = f"INSERT INTO scouting.matches ({col_str}) VALUES ({placeholders})"
            
            # Convert DataFrame rows to list of tuples
            rows = df.values.tolist()
            
            # Use executemany if supported
            con.executemany(sql, rows)
            st.success(f"Uploaded {len(rows)} rows successfully!")
    except Exception as e:
        st.error(f"Error uploading CSV: {e}")