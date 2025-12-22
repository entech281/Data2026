import streamlit as st
from cached_data import get_oprs_and_ranks_for_event
import plotly.express as px
from pages_util.event_selector import event_selector

selected_event = event_selector()

st.title("Rankings")
rankings = get_oprs_and_ranks_for_event(selected_event)
rankings = rankings[['team_number','rank','avg_rp','opr','wins','losses','ties','total_rp','avg_win_rp','avg_auto_rp','avg_coral_rp','avg_barge_rp','dpr','ccwm']]

st.subheader("Rank vs OPR")
fig = px.scatter(rankings,
                 x='opr',
                 y='rank',
                 size_max=15,
                 hover_data=['team_number'],
                 title="Rank Vs OPR")

fig.update_traces(
    text=rankings['team_number'],
    textposition='top right',
    mode='markers+text',
    marker=dict(size=15)
)

fig.update_layout(
    yaxis=dict(autorange='reversed')
)

# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)


st.subheader("Rankings")
st.dataframe( rankings,hide_index=True)
