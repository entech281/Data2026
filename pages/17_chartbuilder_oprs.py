import streamlit as st

from pygwalker.api.streamlit import StreamlitRenderer
from cached_data import get_oprs_and_ranks_for_event
from pages_util.event_selector import event_selector

st.set_page_config(layout="wide")

st.title("Chart Builder-- TBA OPRs")

CACHE_TIME_SECS=240

selected_event = event_selector()

@st.cache_resource(ttl=CACHE_TIME_SECS)
def get_pyg_renderer() -> "StreamlitRenderer":
    df =get_oprs_and_ranks_for_event(selected_event)
    df['team_number'] = df['team_number'].astype(str)
    return StreamlitRenderer(df, spec="./gw2_config.json", spec_io_mode="rw",height=800)

renderer = get_pyg_renderer()

renderer.explorer()