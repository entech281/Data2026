import streamlit as st
from frc_data_281.jobs import scheduler as jobs
from frc_data_281.app.components import get_static_path

st.set_page_config(layout="wide")

st.title("281 Scouting3")

st.subheader("Open the page list if this looks totally blank")

st.caption("""
This is a demo landing page. put stuff you want users to see on here.
A good example might be links, very important data,
or branding information
""")

st.image(get_static_path("281.png"), width=200)
