import streamlit as st

from pygwalker.api.streamlit import StreamlitRenderer
from frc_data_281.db.cached_queries import get_oprs_and_ranks_for_event
from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.app.components import get_config_path

st.set_page_config(layout="wide")

st.title("Chart Builder-- TBA OPRs")

CACHE_TIME_SECS = 240

selected_event = event_selector()


@st.cache_resource(ttl=CACHE_TIME_SECS)
def get_pyg_renderer() -> "StreamlitRenderer":
    df = get_oprs_and_ranks_for_event(selected_event)
    df['team_number'] = df['team_number'].astype(str)
    return StreamlitRenderer(df, spec=get_config_path("gw_opr_config.json"), spec_io_mode="rw", height=800)


renderer = get_pyg_renderer()

renderer.explorer()
