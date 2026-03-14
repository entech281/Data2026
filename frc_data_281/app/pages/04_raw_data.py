import streamlit as st
from frc_data_281.db import cached_queries as cached_data
from frc_data_281.db.connection import get_connection
import base64
from frc_data_281.app.components.event_selector import event_selector
import pandas as pd
import struct

st.set_page_config(layout="wide")

st.title("Team Ranking Based on Selected Characteristics")

selected_event = event_selector()


def bytes_to_base64(byte_array):
    if byte_array is None:
        return ""
    return base64.b64encode(byte_array).decode("utf-8")


def image_formatter(byte_array):
    if byte_array is None:
        return ""
    base64_str = bytes_to_base64(byte_array)
    return f'<img src="data:image/png;base64,{base64_str}" width="100">'


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

# Format image columns in pit data
def convert_to_bytearray(item):
    if item is None:
        return None
    elif isinstance(item, float):
        return bytearray(struct.pack("f", item))
    elif isinstance(item, (bytes, bytearray, memoryview)):
        return bytearray(item)
    else:
        return None

for photo_col in ['auto_route', 'robot_photo']:
    if photo_col in pit.columns:
        pit[photo_col] = pit[photo_col].apply(convert_to_bytearray)
        pit[photo_col] = pit[photo_col].apply(image_formatter)


st.title("Raw Data")

st.header(f"Matches  ({len(matches)})")
st.dataframe(matches, column_config=display_config)

st.header(f"Rankings ({len(rankings)})")
st.dataframe(rankings, column_config=display_config)

st.header(f"Pit ({len(pit)})")
pit_html = pit.to_html(escape=False)
st.html(pit_html)

st.header(f"Match Scouted ({len(match_scouted)}) This is not event Specific")
st.dataframe(match_scouted, column_config=display_config)
