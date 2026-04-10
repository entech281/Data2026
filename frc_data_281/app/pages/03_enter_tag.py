import streamlit as st
import pandas as pd
from frc_data_281.db.connection import get_connection
from frc_data_281.db.cached_queries import get_team_list
from frc_data_281.app.components.event_selector import event_selector

st.set_page_config(layout="wide")
st.title("Team Tags")
st.caption("Upvote/downvote team attributes. Tags with more upvotes appear at the top.")

selected_event = event_selector()

team_list = get_team_list(selected_event)
available_tags = [
    "Good Driver", "Bad Driver", "Unreliable", "Fast", "Normal-Speed", "Slow", "Pizza Box", "Disable"
]

col1, col2, col3 = st.columns(3)
with col1:
    selected_team = st.selectbox("Team Number", team_list)
with col2:
    selected_tag = st.selectbox("Tag", available_tags)
with col3:
    st.write("")
    confirm = st.button('Add/Vote Up', width='stretch')

if confirm:
    with get_connection() as con:
        # UPSERT: insert if not exists, increment upvotes if exists
        con.execute("""
            INSERT INTO scouting.tags (event_key, team_number, tag, upvotes, downvotes)
            VALUES (?, ?, ?, 1, 0)
            ON CONFLICT(event_key, team_number, tag) DO UPDATE SET
            upvotes = upvotes + 1
        """, [selected_event, selected_team, selected_tag])
    st.success(f'Voted for "{selected_tag}" on Team {selected_team}!', icon="✅")
    st.rerun()

st.divider()
st.subheader("All Tags (sorted by net score)")

# Fetch all tags with calculated net score, sorted by net score descending
with get_connection() as con:
    all_tags_df = con.sql("""
        SELECT 
            team_number,
            tag,
            upvotes,
            downvotes,
            (upvotes - downvotes) as net_score
        FROM scouting.tags
        WHERE event_key = ?
        ORDER BY net_score DESC, team_number, tag
    """, params=[selected_event]).df()

if all_tags_df.empty:
    st.info("No tags yet. Add one above!")
else:
    # Display tags in columns: Team | Tag | Upvotes | Downvotes | Net Score | Actions
    cols = st.columns([1, 2, 1, 1, 1, 1.5])
    with cols[0]:
        st.write("**Team**")
    with cols[1]:
        st.write("**Tag**")
    with cols[2]:
        st.write("**👍**")
    with cols[3]:
        st.write("**👎**")
    with cols[4]:
        st.write("**Net**")
    with cols[5]:
        st.write("**Actions**")

    st.divider()

    for _, row in all_tags_df.iterrows():
        team = int(row['team_number'])
        tag = row['tag']
        upvotes = int(row['upvotes'])
        downvotes = int(row['downvotes'])
        net = int(row['net_score'])

        cols = st.columns([1, 2, 1, 1, 1, 1.5])
        with cols[0]:
            st.write(f"{team}")
        with cols[1]:
            st.write(tag)
        with cols[2]:
            st.write(str(upvotes))
        with cols[3]:
            st.write(str(downvotes))
        with cols[4]:
            if net > 0:
                st.write(f"🟢 +{net}")
            elif net < 0:
                st.write(f"🔴 {net}")
            else:
                st.write("⚪ 0")
        with cols[5]:
            col_up, col_down = st.columns(2)
            with col_up:
                if st.button("👍", key=f"up_{selected_event}_{team}_{tag}", width='stretch'):
                    with get_connection() as con:
                        con.execute(
                            "UPDATE scouting.tags SET upvotes = upvotes + 1 WHERE event_key = ? AND team_number = ? AND tag = ?",
                            [selected_event, team, tag]
                        )
                    st.rerun()
            with col_down:
                if st.button("👎", key=f"down_{selected_event}_{team}_{tag}", width='stretch'):
                    with get_connection() as con:
                        con.execute(
                            "UPDATE scouting.tags SET downvotes = downvotes + 1 WHERE event_key = ? AND team_number = ? AND tag = ?",
                            [selected_event, team, tag]
                        )
                    st.rerun()
