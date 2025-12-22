import streamlit as st
from pages_util.event_selector import event_selector
from cached_data import get_matches, get_team_list, get_oprs_and_ranks_for_event
from opr3 import *
import altair as alt
from PIL import Image
import io
from pages_util.style import st_horizontal
import duckdb
from opr3 import add_zscores

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
# ranking_df = con.sql(f"""
# SELECT  er.team_number,
#         er.rank as actual_rank,
#         o.oprs,
#         er.event_key,
#         RANK() OVER (ORDER BY oprs DESC) as expected_rank
# FROM tba.event_rankings er
# INNER JOIN tba.oprs o ON (er.team_number = o.team_number AND er.event_key = o.event_key)
# """).df()

ranking_df = get_oprs_and_ranks_for_event(selected_event)
ranking_df = duckdb.query("SELECT *, RANK() OVER (ORDER BY opr DESC) as expected_rank FROM ranking_df").df()

team = st.selectbox("Team Number", team_list, format_func=lambda team: int(team))

if team is not None:
    # team_ranking = ranking_df[(ranking_df['team_number'] == team) & (ranking_df['event_key'].isin([selected_event]))]
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

if team is not None and events is not None and len(events) > 0:
    st.subheader(f"Team {team} Performance")

    # Get matches for team
    team_matches = matches_df[
        ((matches_df['red1'] == team) | (matches_df['red2'] == team) | (matches_df['red3'] == team) |
         (matches_df['blue1'] == team) | (matches_df['blue2'] == team) | (matches_df['blue3'] == team)) &
        (matches_df['event_key'].isin(events))
    ].sort_values(['event_key', 'match_number'])

    # Calculate running stats for each match
    match_stats = []
    for i in range(1, len(team_matches) + 1):
        match_slice = team_matches.iloc[:i]

        raw_stats = calculate_raw_opr(match_slice)
        numeric_cols = raw_stats.select_dtypes(include=['float64', 'int64']).columns
        numeric_cols = [col for col in numeric_cols if col not in ['team_id', 'match_num']]
        with_z = add_zscores(raw_stats, numeric_cols)

        with_z['match_num'] = i
        with_z = with_z[with_z['team_id'] == team]
        with_z = with_z.fillna(0)

        match_stats.append(with_z)


    team_stats = pd.DataFrame()
    # Combine match stats
    if len(match_stats) > 0:
        team_stats = pd.concat(match_stats)

    # st.write(f"Stats shape: {team_stats.shape}")  # Debug

    # Select metrics and their z-scores
    base_metrics = [col for col in team_stats.columns 
                   if col not in ['team_id', 'margin', 'their_score', 'match_num']
                   and not col.endswith('_z')]

    # Create chart dataframe
    chart_df = pd.DataFrame({"Metric": [], "Trend": []})

    # Add both raw and z-score metrics
    for metric in base_metrics:
        raw_values = team_stats[metric].tolist()
        z_values = team_stats[f"{metric}_z"].tolist()

        chart_df = pd.concat([
            chart_df,
            pd.DataFrame({
                "Metric": [f"{metric} (Raw)", f"{metric} (Z-Score)"],
                "Trend": [raw_values, z_values]
            })
        ], ignore_index=True)

    st.dataframe(
        chart_df,
        column_config={
            "Metric": "Performance Metric",
            "Trend": st.column_config.LineChartColumn(
                "Performance Over Time",
                width="medium"
            )
        },
        hide_index=True
    )
"""
    
avg_coral_df = con.sql("""SELECT 
    m.team_number,
    AVG(m.auto_coral_level_1) AS avg_auto_coral_level_1,
    AVG(m.auto_coral_level_2) AS avg_auto_coral_level_2,
    AVG(m.auto_coral_level_3) AS avg_auto_coral_level_3,
    AVG(m.auto_coral_level_4) AS avg_auto_coral_level_4,
    AVG(m.coral_level_1) AS avg_teleop_coral_level_1,
    AVG(m.coral_level_2) AS avg_teleop_coral_level_2,
    AVG(m.coral_level_3) AS avg_teleop_coral_level_3,
    AVG(m.coral_level_4) AS avg_teleop_coral_level_4
FROM scouting.matches m
GROUP BY m.team_number
ORDER BY m.team_number;""").df()

avg_coral_df = add_zscores(avg_coral_df, avg_coral_df.columns[1:])

avg_coral_df = avg_coral_df[avg_coral_df['team_number'] == team]

if not avg_coral_df.empty:
    # Extract auto and teleop z-scores for levels 1–4 as lists.
    auto_vals = avg_coral_df[["avg_auto_coral_level_1_z",
                              "avg_auto_coral_level_2_z",
                              "avg_auto_coral_level_3_z",
                              "avg_auto_coral_level_4_z"]].iloc[0].tolist()
    
    teleop_vals = avg_coral_df[["avg_teleop_coral_level_1_z",
                                "avg_teleop_coral_level_2_z",
                                "avg_auto_coral_level_3_z",
                                "avg_teleop_coral_level_4_z"]].iloc[0].tolist()
    
    # Create a new DataFrame with index as levels "L1" to "L4" and columns "Auto" and "Teleop"
    coral_table = pd.DataFrame({
        "Auto": auto_vals,
        "Teleop": teleop_vals
    }, index=["L1", "L2", "L3", "L4"])
    
    st.dataframe(coral_table)
else:
    st.info("No coral data available for this team.")


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
        st.image("./static/squirrel.png", width=75)
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
        if pit_df['auto_route'].iloc[0] is not None:
            st.subheader("🤖 Auto Route")
            st.image(Image.open(io.BytesIO(pit_df['auto_route'].iloc[0])), use_container_width=True)

        # Notes section
        if pit_df['notes'].iloc[0]:
            st.subheader("📌 Notes")
            st.info(pit_df['notes'].iloc[0])

        # Metadata
        st.caption(
            f"Last updated by {pit_df['author'].iloc[0]} on {pit_df['created_at'].iloc[0].strftime('%Y-%m-%d %H:%M')}")

    else:
        st.info("No pit scouting data available for this team yet")