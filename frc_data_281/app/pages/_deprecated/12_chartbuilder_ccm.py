import pandas as pd
import pygwalker as pyg
import streamlit as st
from frc_data_281.analysis import opr as opr3
from pygwalker.api.streamlit import StreamlitRenderer
from frc_data_281.app.components import get_config_path

st.set_page_config(layout="wide")

st.title("Chart Builder-- Match CCM")


# You should cache your pygwalker renderer, if you don't want your memory to explode
@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df = opr3.get_ccm_data()
    df['team_id'] = df['team_id'].astype(str)
    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    return StreamlitRenderer(df, spec=get_config_path("gw_ccm_config.json"), spec_io_mode="rw", height=800)


renderer = get_pyg_renderer()

renderer.explorer()
