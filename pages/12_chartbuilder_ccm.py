import pandas as pd
import pygwalker as pyg
import streamlit as st
import opr3
from pygwalker.api.streamlit import StreamlitRenderer

st.set_page_config(layout="wide")

st.title("Chart Builder-- Match CCM")


# You should cache your pygwalker renderer, if you don't want your memory to explode
@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df =opr3.get_ccm_data()
    df['team_id'] = df['team_id'].astype(str)
    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    #df = pd.melt(df, id_vars=['team_id','batch'],var_name='attribute',value_name='weighted_score')
    return StreamlitRenderer(df, spec="./gw_config.json", spec_io_mode="rw",height=800)

renderer = get_pyg_renderer()

renderer.explorer()


