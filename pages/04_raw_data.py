import streamlit as st
import cached_data
from motherduck import con
import base64
from pages_util.event_selector import event_selector
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
    base64_str = bytes_to_base64(byte_array)
    return f'<img src="data:image/png;base64,{base64_str}" width="200">'

display_config = {
    'id': st.column_config.NumberColumn("Id", format="%d"),
    'start': st.column_config.DatetimeColumn('Start', format="D MMM YYYY, h:mm a"),
    'end': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'started': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'updated_at': st.column_config.DatetimeColumn('End', format="D MMM YYYY, h:mm a"),
    'event_id': st.column_config.NumberColumn("Id", format="%d"),
    'auto_route': st.column_config.Column("Auto Route")
}

#getting these from cache-- so that we can save database resources
# in production, we'd cache things that dont change often

matches= cached_data.get_matches_for_event(selected_event)  #this one is not executed each page refresh.
rankings = cached_data.get_tba_oprs_and_ranks_for_event(selected_event)

pit = con.sql("SELECT * FROM scouting.pit").df()
match_scouted = con.sql("SELECT * FROM scouting.matches").df()

# Format images in pit data
if 'auto_route' in pit.columns:
    pit['auto_route'] = pit['auto_route'].apply(lambda item: bytearray(struct.pack("f", item) if type(item) is float else item))
    pit['auto_route'] = pit['auto_route'].apply(image_formatter)


st.title("Raw Data")

st.header(f"Matches  ({len(matches)})")
st.dataframe(matches,column_config=display_config)

st.header(f"Rankings ({len(rankings)})")
st.dataframe(rankings,column_config=display_config)

st.header(f"Pit ({len(pit)})")
st.markdown(pit.to_html(escape=False), unsafe_allow_html=True)

st.header(f"Match Scouted ({len(match_scouted)}) This is not event Specific")
st.dataframe(match_scouted,column_config=display_config)
