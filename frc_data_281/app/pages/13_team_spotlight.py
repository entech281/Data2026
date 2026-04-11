import streamlit as st
from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.db.cached_queries import get_matches, get_team_list, get_oprs_and_ranks_for_event
from frc_data_281.analysis.opr import (
    get_ccm_data_for_event,
    select_z_score_columns,
    select_non_zscore_columns,
    add_zscores
)
from frc_data_281.db.connection import get_connection
import altair as alt
from PIL import Image
import io
from frc_data_281.app.components.style import st_horizontal
import duckdb
import pandas as pd
import pandas as pd
from frc_data_281.app.components import get_static_path

selected_event = event_selector()
st.title("Team Spotlight")

team_list = get_team_list(selected_event)

# TODO
# Make all of these one one sql statement

matches_df = get_matches()
with get_connection() as con:
    tags_df = con.sql(f"""SELECT te.team_number, count(ta.tag), ta.tag
                        FROM tba.teams te
                        LEFT JOIN scouting.tags ta ON
                        (ta.team_number = te.team_number)
                        GROUP BY te.team_number, ta.tag;""").df()
    pit_df = con.sql("SELECT * FROM scouting.pit").df()

ranking_df = get_oprs_and_ranks_for_event(selected_event)
ranking_df = duckdb.query("SELECT *, RANK() OVER (ORDER BY opr DESC) as expected_rank FROM ranking_df").df()

team = st.selectbox("Team Number", team_list, format_func=lambda team: str(int(team)))

if team is not None:
    team_ranking = ranking_df[(ranking_df['team_number'] == team)]
    if not team_ranking.empty:

        with st.container(border=True):
            st.subheader("Rankings Analysis")
            col1, col2, col3 = st.columns(3)

            with col1:
                if pd.notna(team_ranking['opr'].iloc[0]):
                    st.metric("OPR", f"{team_ranking['opr'].iloc[0]:.2f}")
                else:
                    st.info("No OPR data available")

            with col2:
                if pd.notna(team_ranking['rank'].iloc[0]):
                    st.metric("Current Rank", int(team_ranking['rank'].iloc[0]))
                else:
                    st.info("No ranking data available")

            with col3:
                if pd.notna(team_ranking['rank'].iloc[0]) and pd.notna(team_ranking['expected_rank'].iloc[0]):
                    rank_diff = int(team_ranking['rank'].iloc[0]) - int(team_ranking['expected_rank'].iloc[0])
                    status = "Underranked" if rank_diff > 0 else "Overranked" if rank_diff < 0 else "Accurately ranked"
                    delta = rank_diff
                    st.metric("Ranking Status", status, delta=f"{delta} positions")
                else:
                    st.info("Cannot calculate ranking difference")
    else:
        st.info("No ranking info")

old_code = """
this duplicates a lot of code already in opr3.
also we realized we need to display the data very
differently based on watching a day of matches.
see new proprosed version
"""

with get_connection() as con:
    avg_hub_df = con.sql("""SELECT
        team_number,
        AVG(hub_score_auto_count) AS avg_hub_auto_count,
        AVG(hub_score_teleop_count) AS avg_hub_teleop_count,
        AVG(hub_score_total_count) AS avg_hub_total_count,
        AVG(auto_tower_points) AS avg_auto_tower_points,
        AVG(end_game_tower_points) AS avg_end_game_tower_points
    FROM (
        SELECT
            blue1 AS team_number,
            blue_hub_score_auto_count AS hub_score_auto_count,
            blue_hub_score_teleop_count AS hub_score_teleop_count,
            blue_hub_score_total_count AS hub_score_total_count,
            blue_auto_tower_points AS auto_tower_points,
            blue_end_game_tower_points AS end_game_tower_points
        FROM tba.matches WHERE event_key = '""" + selected_event + """'
        UNION ALL
        SELECT blue2, blue_hub_score_auto_count, blue_hub_score_teleop_count, blue_hub_score_total_count, blue_auto_tower_points, blue_end_game_tower_points FROM tba.matches WHERE event_key = '""" + selected_event + """'
        UNION ALL
        SELECT blue3, blue_hub_score_auto_count, blue_hub_score_teleop_count, blue_hub_score_total_count, blue_auto_tower_points, blue_end_game_tower_points FROM tba.matches WHERE event_key = '""" + selected_event + """'
        UNION ALL
        SELECT red1, red_hub_score_auto_count, red_hub_score_teleop_count, red_hub_score_total_count, red_auto_tower_points, red_end_game_tower_points FROM tba.matches WHERE event_key = '""" + selected_event + """'
        UNION ALL
        SELECT red2, red_hub_score_auto_count, red_hub_score_teleop_count, red_hub_score_total_count, red_auto_tower_points, red_end_game_tower_points FROM tba.matches WHERE event_key = '""" + selected_event + """'
        UNION ALL
        SELECT red3, red_hub_score_auto_count, red_hub_score_teleop_count, red_hub_score_total_count, red_auto_tower_points, red_end_game_tower_points FROM tba.matches WHERE event_key = '""" + selected_event + """'
    )
    GROUP BY team_number
    ORDER BY team_number;""").df()

avg_hub_df = add_zscores(avg_hub_df, avg_hub_df.columns[1:])
avg_hub_df = avg_hub_df[avg_hub_df['team_number'] == team]

if not avg_hub_df.empty:
    hub_table = pd.DataFrame({
        "Avg Count": [
            avg_hub_df['avg_hub_auto_count_z'].iloc[0],
            avg_hub_df['avg_hub_teleop_count_z'].iloc[0],
            avg_hub_df['avg_hub_total_count_z'].iloc[0],
        ],
        "Avg Tower Pts (z)": [
            avg_hub_df['avg_auto_tower_points_z'].iloc[0],
            avg_hub_df['avg_end_game_tower_points_z'].iloc[0],
            None,
        ],
    }, index=["Auto Hub", "Teleop Hub", "Total Hub"])
    st.subheader("🎯 Hub & Tower Scoring (z-score)")
    st.dataframe(hub_table)
else:
    st.info("No hub scoring data available for this team.")


if team is not None:

    st.subheader("Tags")

    # Create pivot table
    pivot_df = tags_df[tags_df['team_number'] == team].pivot_table(
        index='team_number',
        columns='tag',
        values='count(ta.tag)',
        fill_value=0
    ).reset_index()

    # Melt for Altair visualization
    chart_df = pivot_df.melt(
        id_vars=['team_number'],
        var_name='tag',
        value_name='count'
    )

    # Create chart
    c = alt.Chart(chart_df).mark_bar().encode(
        x='tag:N',
        y='count:Q'
    )

    if pivot_df.empty:
        st.info("No tag data to display :slightly_frowning_face:")
        st.info("Here is a squirrel to make you feel less sad")
        st.image(get_static_path("squirrel.png"), width=75)
        st.link_button("Image credit", "https://xkcd.com/1503")
    else:
        st.altair_chart(c)

    pit_df = pit_df[(pit_df['team_number']) == team]
    if not pit_df.empty:
        st.divider()
        st.subheader("📝 Pit Scouting Data")

        col1, col2, col3 = st.columns(3)

        prefered_scoring = str(", ".join(pit_df['preferred_scoring'].iloc[-1].split(','))).removeprefix(
            "[").removesuffix("]")

        with col1:
            with st_horizontal():
                st.metric("Height", f"{pit_df['height'].iloc[0]}\"")
                st.metric("Width", f"{pit_df['width'].iloc[0]}\"")

        with col2:
            with st_horizontal():
                st.metric("Length", f"{pit_df['length'].iloc[0]}\"")
                st.metric("Weight", f"{pit_df['weight'].iloc[0]} lbs")

        with col3:
            with st_horizontal():
                st.metric("Preferred Start", pit_df['start_position'].iloc[0])
                st.metric("Preferred Scoring", prefered_scoring)

        # Strategy section
        st.subheader("🎯 Strategy")
        capabilities = pit_df['scoring_capabilities'].iloc[0].split(',')
        st.write("**Scoring Capabilities:**", ", ".join(capabilities))
        st.write("**Preferred Scoring:** ", prefered_scoring)

        # Auto route
        if pd.notna(pit_df['auto_route'].iloc[0]):
            st.subheader("🤖 Auto Route")
            st.image(Image.open(io.BytesIO(pit_df['auto_route'].iloc[0])), width='stretch')

        # Robot photo
        if 'robot_photo' in pit_df.columns and pd.notna(pit_df['robot_photo'].iloc[0]):
            st.subheader("📷 Robot Photo")
            st.image(Image.open(io.BytesIO(pit_df['robot_photo'].iloc[0])), width='stretch')

        # Notes section
        if pit_df['notes'].iloc[0]:
            st.subheader("📌 Notes")
            st.info(pit_df['notes'].iloc[0])

        # Metadata
        st.caption(
            f"Last updated by {pit_df['author'].iloc[0]} on {pit_df['created_at'].iloc[0].strftime('%Y-%m-%d %H:%M')}")

    else:
        st.info("No pit scouting data available for this team yet")

    # --- Match Scouting Data (FSC) ---
    from frc_data_281.db.cached_queries import get_scouting_data_for_teams
    team_scouting = get_scouting_data_for_teams(selected_event, [team])
    if not team_scouting.empty:
        st.divider()
        st.subheader("📊 Match Scouting (FSC)")

        team_scouting = team_scouting.copy()
        team_scouting['total_fuel'] = (
            team_scouting['auto_fuel_score'].fillna(0) +
            team_scouting['teleop_fuel_score'].fillna(0)
        )
        n = len(team_scouting)

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Matches Scouted", n)
        with col_s2:
            avg_auto = team_scouting['auto_fuel_score'].mean()
            st.metric("Avg Auto Fuel", f"{avg_auto:.1f}" if pd.notna(avg_auto) else "—")
        with col_s3:
            avg_teleop = team_scouting['teleop_fuel_score'].mean()
            st.metric("Avg Teleop Fuel", f"{avg_teleop:.1f}" if pd.notna(avg_teleop) else "—")
        with col_s4:
            avg_total = team_scouting['total_fuel'].mean()
            st.metric("Avg Total Fuel", f"{avg_total:.1f}" if pd.notna(avg_total) else "—")

        # Strategy breakdown
        strat_cols = ['strategy_active_scored', 'strategy_active_ferrying', 'strategy_active_defense']
        strat_available = [c for c in strat_cols if c in team_scouting.columns]
        if strat_available and n > 0:
            col_st1, col_st2, col_st3 = st.columns(3)
            labels = {"strategy_active_scored": "Scoring", "strategy_active_ferrying": "Ferrying", "strategy_active_defense": "Defense"}
            for col_w, col_name in zip([col_st1, col_st2, col_st3], strat_cols):
                if col_name in team_scouting.columns:
                    pct = team_scouting[col_name].sum() / n * 100
                    col_w.metric(f"% {labels[col_name]}", f"{pct:.0f}%")

        # Fuel trend sparkline
        import plotly.graph_objects as go_spot
        fig_spark = go_spot.Figure()
        sorted_sc = team_scouting.sort_values('match_number')
        fig_spark.add_trace(go_spot.Scatter(
            x=sorted_sc['match_number'], y=sorted_sc['total_fuel'],
            mode='lines+markers', line=dict(color='#e74c3c', width=2),
            marker=dict(size=5), name='Total Fuel',
        ))
        fig_spark.update_layout(
            title="Total Fuel Over Matches", height=250,
            xaxis_title="Match", yaxis_title="Fuel",
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_spark, use_container_width=True)
