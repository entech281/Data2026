import streamlit as st
from cached_data import get_event_list,get_oprs_and_ranks_for_team,get_team_list
from opr3 import get_ccm_data_for_event_separated
from match_dataset_tools import filter_for_team
import altair as alt
from pages_util.style import  st_horizontal
from pages_util.event_selector import  event_selector
from streamlit_extras.grid import grid
import pandas as pd

event_list = get_event_list()

st.title("Team Spotlight Performance")

with st_horizontal():
    selected_event = event_selector()
    team_list = get_team_list(selected_event)
    team = st.selectbox("Team Number", team_list, format_func=lambda team: int(team))


match_stats_z, match_stats_nonz = get_ccm_data_for_event_separated(selected_event)

match_stats_z = filter_for_team(match_stats_z,team)
match_stats_nonz = filter_for_team(match_stats_z,team)

match_stats_nonz_melted  = pd.melt(match_stats_nonz, id_vars=['team_id'],var_name='attribute',value_name='value')
match_stats_z_melted  = pd.melt(match_stats_z, id_vars=['team_id'],var_name='attribute',value_name='value')

team_stats = get_oprs_and_ranks_for_team(selected_event,team)

if len(match_stats_z) == 0:
    st.caption("No Data For Selected Team somehow. Maybe they have no matches or are not here. ")
    st.stop()

NO_DATA_VALUE=-1.0
st.subheader("Basic Stats")
metric_grid = grid([1,1,1,1,1])
metric_grid.metric("Rank", team_stats.get('rank',NO_DATA_VALUE),border=True)
metric_grid.metric("Avg RP/match", team_stats.get('avg_rp',NO_DATA_VALUE),border=True)
metric_grid.metric("Opr", f"{team_stats.get('opr',NO_DATA_VALUE):.2f}",border=True)
metric_grid.metric("Dpr", f"{team_stats.get('dpr',NO_DATA_VALUE):.2f}",border=True)
metric_grid.metric("Record", f"{team_stats.get('wins',NO_DATA_VALUE)}-{team_stats.get('losses',NO_DATA_VALUE)}-{team_stats.get('ties',NO_DATA_VALUE)}",border=True)

st.subheader("RP Averages Per match")
metric_grid = grid([1,1,1,1,1])
metric_grid.metric('Total',f"{team_stats.get('avg_rp',NO_DATA_VALUE):.2f}")
metric_grid.metric('Win/Tie',f"{team_stats.get('avg_win_rp',NO_DATA_VALUE):.2f}")
metric_grid.metric('Auto',f"{team_stats.get('avg_auto_rp',NO_DATA_VALUE):.2f}")
metric_grid.metric('Coral',f"{team_stats.get('avg_coral_rp',NO_DATA_VALUE):.2f}")
metric_grid.metric('Barge',f"{team_stats.get('avg_barge_rp',NO_DATA_VALUE):.2f}")


st.subheader("Performance: Zscores")

chart = alt.Chart(match_stats_z_melted).mark_circle(size=60).encode(
    x=alt.X('value:Q', title="Zscore"),
    y=alt.Y('attribute:N', title="Attribute",axis=alt.Axis(labelLimit=250)),
    tooltip=['attribute', 'value']
).properties(
    width=400,
    height=1000
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)
