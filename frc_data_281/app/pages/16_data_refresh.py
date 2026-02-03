import logging
import streamlit as st
from frc_data_281.the_blue_alliance import pipeline
from streamlit_extras.streaming_write import write
from streamlit_extras.capture import logcapture
from frc_data_281.db.cached_queries import clear_caches

logger = logging.getLogger(__name__)
st.title("Refresh Data from TBA")

st.header("Press this button to reload match data from TBA")


def run_data_refresh():
    logger = pipeline.everyone_use_the_same_logger()
    logger.setLevel(logging.INFO)
    with logcapture(st.empty().code, from_logger=logger):
        pipeline.set_loop_delay(3)
        pipeline.sync()


if st.button("Refresh data Now"):
    run_data_refresh()
    clear_caches()
    st.write("Cache Cleared")
