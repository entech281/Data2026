import streamlit as st
from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.db.cached_queries import get_matches, get_team_list, get_oprs_and_ranks_for_event
from frc_data_281.analysis.opr import (
    get_ccm_data_for_event,
    select_z_score_columns,
    select_non_zscore_columns,
    add_zscores
)
from frc_data_281.db.connection import con
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

        # Notes section
        if pit_df['notes'].iloc[0]:
            st.subheader("📌 Notes")
            st.info(pit_df['notes'].iloc[0])

        # Metadata
        st.caption(
            f"Last updated by {pit_df['author'].iloc[0]} on {pit_df['created_at'].iloc[0].strftime('%Y-%m-%d %H:%M')}")

    else:
        st.info("No pit scouting data available for this team yet")
