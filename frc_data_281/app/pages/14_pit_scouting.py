import streamlit as st
import pandas as pd
from frc_data_281.db.connection import get_connection
from frc_data_281.analysis import opr as opr3
from frc_data_281.db.cached_queries import get_team_list, get_event_list, get_most_recent_event
from PIL import Image
import io
from frc_data_281.app.components.event_selector import event_selector

st.set_page_config(layout="wide")
st.title("Pit Scouting Form")
selected_event = event_selector()
all_teams = get_team_list(selected_event)

# Refresh existing teams list on every page load (picks up newly submitted forms)
with get_connection() as con:
    existing_teams = con.sql("SELECT DISTINCT team_number FROM scouting.pit").df()['team_number'].tolist()

# Create lists of teams with and without forms
teams_without_forms = [t for t in all_teams if t not in existing_teams]
teams_with_forms = [t for t in all_teams if t in existing_teams]

# Add override checkbox
override = st.checkbox("Update existing pit scouting entry")

if override:
    selected_team = st.selectbox("Team Number", teams_with_forms, key="pit_team")
else:
    selected_team = st.selectbox("Team Number", teams_without_forms, key="pit_team")


def get_default_data(team: int = None) -> pd.DataFrame:
    """
    Retrieve default pit scouting data for a given team.
    """
    # Default pit scouting values
    default = pd.DataFrame([{
        'height': 60,
        'weight': 100,
        'length': 36,
        'width': 36,
        'start_position': "No Preference",
        'drive_type': "",
        'scoring_capabilities': "",
        'preferred_scoring': "",
        'notes': "",
        'auto_route': None,
        'robot_photo': None,
    }])

    if team is not None:
        with get_connection() as con:
            df = con.sql(f"""
                    SELECT * FROM scouting.pit
                    WHERE team_number = {team}
                    ORDER BY created_at DESC LIMIT 1
                """).df()
        if not df.empty:
            # Clean up the string fields
            df['preferred_scoring'] = df['preferred_scoring'].str.removeprefix("[").str.removesuffix("]")
            df['scoring_capabilities'] = df['scoring_capabilities'].str.removeprefix("[").str.removesuffix("]")
            return df
    return default


with st.form("pit_scouting", clear_on_submit=True):
    team = selected_team
    if override and team:
        default_data = get_default_data(team)
    else:
        default_data = get_default_data()

    # Physical Specifications
    col1, col2 = st.columns(2)
    with col1:
        height = st.number_input("Robot Height Extended w/out bumpers (inches)",
                                 min_value=0, max_value=120, step=1,
                                 value=int(default_data['height'].iloc[0]))
        length = st.number_input("Robot Length w/out bumpers (inches)",
                                 min_value=0, max_value=60, step=1,
                                 value=int(default_data['length'].iloc[0]))
    with col2:
        weight = st.number_input("Robot Weight w/out bumpers (lbs)",
                                 min_value=0, max_value=125, step=1,
                                 value=int(default_data['weight'].iloc[0]))
        width = st.number_input("Robot Width w/out bumpers (inches)",
                                min_value=0, max_value=60, step=1,
                                value=int(default_data['width'].iloc[0]))

    start_pos = st.selectbox(
        "Preferred Starting Position",
        ["Left", "Center", "Right", "No Preference"],
        index=["Left", "Center", "Right", "No Preference"].index(default_data['start_position'].iloc[0])
        if default_data['start_position'].iloc[0] in ["Left", "Center", "Right", "No Preference"] else 3
    )

    drive_type_options = ["Mecanum", "Tank", "Swerve", "H Drive", "Other"]
    drive_type = st.selectbox(
        "Drive Type",
        drive_type_options,
        index=drive_type_options.index(default_data['drive_type'].iloc[0])
        if default_data['drive_type'].iloc[0] in drive_type_options else 0
    )

    binary_data = st.camera_input(label="Auto Route (draw a picture please)")
    auto_route = None

    if binary_data is not None:
        binary_data = binary_data.read()
        image_pil = Image.open(io.BytesIO(binary_data))
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='PNG')
        auto_route = img_byte_arr.getvalue()

    if pd.notna(default_data['auto_route'].iloc[0]):
        st.image(Image.open(io.BytesIO(default_data['auto_route'].iloc[0])), caption="Previous Auto Route")

    robot_photo_data = st.camera_input(label="Robot Photo", key="robot_photo_input")
    robot_photo = None

    if robot_photo_data is not None:
        robot_photo_bytes = robot_photo_data.read()
        image_pil = Image.open(io.BytesIO(robot_photo_bytes))
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='PNG')
        robot_photo = img_byte_arr.getvalue()

    if pd.notna(default_data['robot_photo'].iloc[0]):
        st.image(Image.open(io.BytesIO(default_data['robot_photo'].iloc[0])), caption="Previous Robot Photo")

    scoring_possibilities = ["Touching Hub", "Mid Range", "Long shot", "Trench shot",
                             "L1 Climb", "L2 Climb", "L3 Climb", "Snowblow"]

    # Parse defaults and filter to only valid options (handles spacing and mismatches)
    scoring_caps_default = []
    if default_data['scoring_capabilities'].iloc[0]:
        stored_caps = str(default_data['scoring_capabilities'].iloc[0]).split(',')
        scoring_caps_default = [c.strip() for c in stored_caps if c.strip() in scoring_possibilities]

    preferred_scoring_default = []
    if default_data['preferred_scoring'].iloc[0]:
        stored_prefs = str(default_data['preferred_scoring'].iloc[0]).split(',')
        preferred_scoring_default = [p.strip() for p in stored_prefs if p.strip() in scoring_possibilities]

    scoring_capabilities = st.pills(
        "Scoring Capabilities",
        scoring_possibilities,
        default=scoring_caps_default,
        selection_mode="multi"
    )

    preferred_scoring = st.pills(
        "Preferred Scoring Method",
        scoring_possibilities,
        default=preferred_scoring_default,
        selection_mode="multi",
        key="preferred_scoring"
    )

    notes = st.text_area("Additional Notes", value=default_data['notes'].iloc[0])

    author = st.text_input("author initials (no caps or space)")

    submitted = st.form_submit_button("Submit")

    if submitted:
        # Create data for insertion/update
        data = {
            'team_number': team,
            'height': height,
            'weight': weight,
            'length': length,
            'width': width,
            'start_position': start_pos,
            'drive_type': drive_type,
            'auto_route': auto_route,
            'robot_photo': robot_photo,
            'scoring_capabilities': ','.join(scoring_capabilities),
            'preferred_scoring': ','.join(preferred_scoring) if isinstance(preferred_scoring, list) else preferred_scoring,
            'notes': notes,
            'author': author
        }

        try:
            if override:
                # Update existing row for the team
                with get_connection() as con:
                    con.execute("""
                        UPDATE scouting.pit
                        SET height = ?,
                            weight = ?,
                            length = ?,
                            width = ?,
                            start_position = ?,
                            drive_type = ?,
                            auto_route = ?,
                            robot_photo = ?,
                            scoring_capabilities = ?,
                            preferred_scoring = ?,
                            notes = ?,
                            author = ?,
                            created_at = CURRENT_TIMESTAMP
                        WHERE team_number = ?
                    """, [
                        data['height'], data['weight'], data['length'], data['width'],
                        data['start_position'], data['drive_type'], data['auto_route'], data['robot_photo'],
                        data['scoring_capabilities'],
                        data['preferred_scoring'], data['notes'], data['author'],
                        data['team_number']
                    ])
                st.success("Data updated successfully!")
                # Clear the selectbox selection to refresh the team list
                if "pit_team" in st.session_state:
                    del st.session_state["pit_team"]
            else:
                # Insert new row for the team
                with get_connection() as con:
                    con.execute("""
                        INSERT INTO scouting.pit
                        (team_number, height, weight, length, width,
                        start_position, drive_type, auto_route, robot_photo, scoring_capabilities,
                        preferred_scoring, notes, author)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        data['team_number'], data['height'], data['weight'],
                        data['length'], data['width'], data['start_position'], data['drive_type'],
                        data['auto_route'], data['robot_photo'], data['scoring_capabilities'],
                        data['preferred_scoring'], data['notes'], data['author']
                    ])
                st.success("Data saved successfully!")
                # Clear the selectbox selection to refresh the team list
                if "pit_team" in st.session_state:
                    del st.session_state["pit_team"]
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
