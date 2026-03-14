import streamlit as st
from frc_data_281.db import cached_queries as cached_data
from frc_data_281.db.connection import get_connection
import base64
from frc_data_281.app.components.event_selector import event_selector
import pandas as pd

st.set_page_config(layout="wide")

st.title("Team Ranking Based on Selected Characteristics")

selected_event = event_selector()


def bytes_to_data_uri(byte_array):
    """Convert raw image bytes to a data URI string for Streamlit ImageColumn."""
    if byte_array is None:
        return None
    if isinstance(byte_array, (bytes, bytearray, memoryview)):
        b64 = base64.b64encode(bytes(byte_array)).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    return None


display_config = {
    'id': st.column_config.NumberColumn("Id", format="%d"),
    'start': st.column_config.DatetimeColumn('Start', format="D MMM YYYY, h:mm a"),
    'end': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'started': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'updated_at': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'event_id': st.column_config.NumberColumn("Id", format="%d"),
    'auto_route': st.column_config.Column("Auto Route")
}

# getting these from cache-- so that we can save database resources
# in production, we'd cache things that dont change often

matches = cached_data.get_matches_for_event(selected_event)  # this one is not executed each page refresh.
rankings = cached_data.get_tba_oprs_and_ranks_for_event(selected_event)

with get_connection() as con:
    pit = con.sql("SELECT * FROM scouting.pit").df()
    match_scouted = con.sql("SELECT * FROM scouting.matches").df()

# Convert image BLOB columns to data URIs for Streamlit ImageColumn
for photo_col in ['auto_route', 'robot_photo']:
    if photo_col in pit.columns:
        pit[photo_col] = pit[photo_col].apply(
            lambda x: bytes_to_data_uri(x) if pd.notna(x) else None
        )


st.title("Raw Data")

st.header(f"Matches  ({len(matches)})")
st.dataframe(matches, column_config=display_config)

st.header(f"Rankings ({len(rankings)})")
st.dataframe(rankings, column_config=display_config)

pit_display_config = {
    **display_config,
    'auto_route': st.column_config.ImageColumn("Auto Route"),
    'robot_photo': st.column_config.ImageColumn("Robot Photo"),
}

st.header(f"Pit ({len(pit)})")
st.dataframe(pit, column_config=pit_display_config)

st.header(f"Match Scouted ({len(match_scouted)}) This is not event Specific")
st.dataframe(match_scouted, column_config=display_config)
