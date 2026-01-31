import streamlit as st
from frc_data_281.db.cached_queries import get_event_list, get_most_recent_event


def event_selector():
    event_list = get_event_list()
    selected_event = st.pills("Event", event_list, default=get_most_recent_event(), selection_mode="single")
    if selected_event is None:
        st.caption("Select an Event")
        st.stop()
    else:
        return selected_event
