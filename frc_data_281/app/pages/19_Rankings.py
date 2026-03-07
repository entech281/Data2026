import streamlit as st
from frc_data_281.db.cached_queries import get_oprs_and_ranks_for_event
import plotly.express as px
from frc_data_281.app.components.event_selector import event_selector

selected_event = event_selector()

st.title("Rankings")
rankings = get_oprs_and_ranks_for_event(selected_event)

season = int(selected_event[:4]) if selected_event else 2026
if season >= 2026:
    bonus_cols = ['avg_energized_rp', 'avg_supercharged_rp', 'avg_traversal_rp']
else:
    bonus_cols = ['avg_auto_rp', 'avg_coral_rp', 'avg_barge_rp']

display_cols = ['team_number', 'rank', 'avg_rp', 'opr', 'wins', 'losses', 'ties', 'total_rp', 'avg_win_rp'] + bonus_cols + ['dpr', 'ccwm']
display_cols = [c for c in display_cols if c in rankings.columns]
rankings = rankings[display_cols]

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
st.plotly_chart(fig, width='stretch')


st.subheader("Rankings")
st.dataframe(rankings, hide_index=True)
