import streamlit as st
import pandas as pd
import altair as alt
import opr3
from pages_util.event_selector import event_selector

st.title("Team Ranking Based on Selected Characteristics")

selected_event = event_selector()


df = opr3.get_ccm_data_for_event(selected_event)
df = opr3.select_z_score_columns(df, ['team_id'])

def compute_weighted_score(df, selected_chars, weights):
    weighted_scores = df[selected_chars].mul(weights).sum(axis=1)
    df['weighted_score'] = weighted_scores
    df = df.sort_values(by='weighted_score', ascending=False)
    df['rank'] = df.reset_index().index  # Ensure continuous ranking without gaps
    return df


def computed_weighted_components(original,selected_metrics, weights ):
    selected_metrics = original[selected_metrics]
    weighted = selected_metrics.mul(weights)
    #weighted['total_z'] = weighted.sum(axis=1)
    all = pd.concat([original[['team_id']], weighted],axis=1)
    all['team_id'] = all['team_id'].astype('str')
    #all = all.sort_values(by='total_z', ascending=False)
    #all['rank'] = all['total_z'].rank(ascending=False)
    all = pd.melt(all, id_vars=['team_id'],var_name='attribute',value_name='weighted_score')
    return all



# Select characteristics
available_chars = sorted([col for col in df.columns if col != "team_id"])
selected_chars = st.pills("Select Characteristics", options=available_chars, default=['score_z'], selection_mode="multi")

if len(selected_chars) == 0:
    st.header ("Select at least one characteristic and one Event")
    st.stop()

weights = {}
for char in selected_chars:
    weights[char] = st.slider(f"Weight for {char}", min_value=-1.0, max_value=1.0, value=0.0, step=0.1)

# Compute weighted scores
df_ranked = computed_weighted_components(df, selected_chars, weights)

team_order = df_ranked.groupby('team_id')['weighted_score'].sum().reset_index().sort_values('weighted_score', ascending=False)
sorted_teams = team_order['team_id'].tolist()
# Show bar chart
c = (
    alt.Chart(df_ranked)
    .mark_bar().encode(
        alt.Y('team_id:N', sort=sorted_teams, title="Team"),
        x='weighted_score:Q',
        color=alt.Color('attribute', sort='descending')
    )
)
st.altair_chart(c, use_container_width=True)

st.dataframe(df_ranked,height=600,hide_index=True)