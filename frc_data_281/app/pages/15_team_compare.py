import streamlit as st
from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.db.cached_queries import get_team_list, get_oprs_and_ranks_for_event
from frc_data_281.analysis import opr as opr3
from frc_data_281.db.connection import get_connection
from frc_data_281.app.components import get_static_path

st.title("Team Comparison")
selected_event = event_selector()
team_list = get_team_list(selected_event)

# Team selection
col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team 1", team_list, key="team1")
with col2:
    team2 = st.selectbox("Team 2", team_list, key="team2")

if not team1 or not team2:
    st.caption("Select Two teams to continue")
    st.stop()


event_rankings = get_oprs_and_ranks_for_event(selected_event)
# Rankings comparison
st.subheader("Rankings Comparison")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)

    if event_rankings.loc[event_rankings['team_number'] == team1, 'opr'].empty:
        st.info(f"Sorry, looks like I don't have any info for team {team1}")
        st.stop()

    if event_rankings.loc[event_rankings['team_number'] == team2, 'opr'].empty:
        st.info(f"Sorry, looks like I don't have any info for team {team2}")
        st.stop()

    t1_opr = float(event_rankings.loc[event_rankings['team_number'] == team1, 'opr'].iloc[0])
    t2_opr = float(event_rankings.loc[event_rankings['team_number'] == team2, 'opr'].iloc[0])
    t1_rank = int(event_rankings.loc[event_rankings['team_number'] == team1, 'rank'].iloc[0])
    t2_rank = int(event_rankings.loc[event_rankings['team_number'] == team2, 'rank'].iloc[0])

    # Compute delta for OPR
    delta_opr = t1_opr - t2_opr
    if delta_opr > 0:
        opr_status = f"Team {team1} leads"
    elif delta_opr < 0:
        opr_status = f"Team {team2} leads"
    else:
        opr_status = "Tied"

    # Compute delta for Rank. (Lower rank is better.)
    delta_rank = t2_rank - t1_rank
    if delta_rank > 0:
        rank_status = f"Team {team1} leads"
    elif delta_rank < 0:
        rank_status = f"Team {team2} leads"
    else:
        rank_status = "Tied"

    with col1:
        st.metric("OPR Difference", f"{abs(t1_opr - t2_opr):.1f}", delta=opr_status)
    with col2:
        st.write("Idk what to put here yet")
        st.image(get_static_path("squirrel.png"), width=50)
    with col3:
        st.metric("Rank Difference", abs(t1_rank - t2_rank), delta=f"{rank_status}")

with st.container(border=True):
    # Overall Average Rankings Section
    st.subheader("Overall Average Rankings")
    # Filter rankings for the selected events and teams
    team1_all = event_rankings[event_rankings['team_number'] == team1]
    team2_all = event_rankings[event_rankings['team_number'] == team2]

    if not team1_all.empty and not team2_all.empty:
        avg_team1 = team1_all[['opr', 'rank']].mean()
        avg_team2 = team2_all[['opr', 'rank']].mean()

        col1, col2, col3 = st.columns(3)

        # OPR Comparison for overall averages
        delta_opr_avg = avg_team1['opr'] - avg_team2['opr']
        if delta_opr_avg > 0:
            overall_opr_status = f"Team {team1} leads"
        elif delta_opr_avg < 0:
            overall_opr_status = f"Team {team2} leads"
        else:
            overall_opr_status = "Tied"

        # Rank Comparison for overall averages (note: lower is better)
        delta_rank_avg = avg_team2['rank'] - avg_team1['rank']
        if delta_rank_avg > 0:
            overall_rank_status = f"Team {team1} leads"
        elif delta_rank_avg < 0:
            overall_rank_status = f"Team {team2} leads"
        else:
            overall_rank_status = "Tied"

        with col1:
            st.metric("Avg OPR Difference", f"{abs(delta_opr_avg):.1f}", delta=overall_opr_status)
        with col2:
            st.write("Idk what to put here yet")
            st.image(get_static_path("squirrel.png"), width=50)
        with col3:
            st.metric("Avg Rank Difference", f"{abs(delta_rank_avg):.1f}", delta=overall_rank_status)
    else:
        st.info("Insufficient overall rankings data for one or both teams.")


# Pit data comparison
st.subheader("Robot Specifications")
with get_connection() as con:
    pit_df = con.execute("""
        SELECT * FROM scouting.pit
        WHERE team_number IN (?, ?)
        ORDER BY created_at DESC
    """, [team1, team2]).df()

if not pit_df.empty:
    specs = ['height', 'weight', 'length', 'width']
    for spec in specs:
        col1, col2 = st.columns(2)
        with col1:
            if not pit_df[pit_df['team_number'] == team1].empty:
                value = pit_df[pit_df['team_number'] == team1][spec].iloc[0]
                st.metric(f"Team {team1} {spec}", value)
        with col2:
            if not pit_df[pit_df['team_number'] == team2].empty:
                value = pit_df[pit_df['team_number'] == team2][spec].iloc[0]
                st.metric(f"Team {team2} {spec}", value)

else:
    st.info(f"No specs data to display for teams {team1} and {team2} :slightly_frowning_face:")
    st.info("Here is a squirrel to make you feel less sad")
    st.image(get_static_path("squirrel.png"), width=75)
    st.link_button("Image credit (Click me)", "https://xkcd.com/1503")
