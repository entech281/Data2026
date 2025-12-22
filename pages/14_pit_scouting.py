import streamlit as st
import pandas as pd
from motherduck import con
from opr3 import *
from cached_data import get_team_list,get_event_list,get_most_recent_event
from PIL import Image
import io
from pages_util.event_selector import event_selector

st.title("Pit Scouting Form")
selected_event = event_selector()
all_teams = get_team_list(selected_event)
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

    If a team number is provided and a pit scouting entry exists for that team,
    this function returns a DataFrame with the latest data from the database,
    cleaning up the scoring_capabilities and preferred_scoring fields.
    If no team is provided or there is no existing entry, a DataFrame with default
    pit scouting values is returned.

    Parameters:
        team (int, optional): The team number. Defaults to None.

    Returns:
        pd.DataFrame: A DataFrame containing default pit scouting data.
    """
    # Default pit scouting values
    default = pd.DataFrame([{
        'height': 60,
        'weight': 100,
        'length': 36,
        'width': 36,
        'start_position': "No Preference",
        'scoring_capabilities': "",
        'preferred_scoring': "",
        'notes': "",
        'auto_route': None
    }])
    
    if team is not None:
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

with st.form("pit_scouting"):
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
        ["Climb Side", "Center", "Processor Side", "No Preference"],
        index=["Climb Side", "Center", "Processor Side", "No Preference"].index(default_data['start_position'].iloc[0])
    )
    
    # Auto Route

    
    # image = Image.open(io.BytesIO(binary_data))
    # img_byte_arr = io.BytesIO()
    # image.save(img_byte_arr, format='PNG')
    # img_byte_arr = img_byte_arr.getvalue()
    

    binary_data = st.camera_input(label="Auto Route (draw a picture please)")
    auto_route = None
    
    if binary_data is not None:
        binary_data = binary_data.read()
        image_pil = Image.open(io.BytesIO(binary_data))
        img_byte_arr = io.BytesIO()
        image_pil.save(img_byte_arr, format='PNG')
        auto_route = img_byte_arr.getvalue()
    
    if default_data['auto_route'].iloc[0] is not None:
        st.image(Image.open(io.BytesIO(default_data['auto_route'].iloc[0])), caption="Previous Auto Route")
    
    scoring_possibilities = ["Coral L1", "Coral L2", "Coral L3", "Coral L4", 
                           "Processor", "Barge", "Deep Climb", "Shallow Climb"]

    scoring_capabilities = st.pills(
        "Scoring Capabilities",
        scoring_possibilities,
        default=default_data['scoring_capabilities'].iloc[0].split(',') if default_data['scoring_capabilities'].iloc[0] else [],
        selection_mode="multi"
    )
    
    preferred_scoring = st.pills(
        "Preferred Scoring Method",
        scoring_possibilities,
        default=default_data['preferred_scoring'].iloc[0].split(', ') if default_data['preferred_scoring'].iloc[0] else [],
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
            'auto_route': auto_route,
            'scoring_capabilities': ','.join(scoring_capabilities),
            'preferred_scoring': ','.join(preferred_scoring) if isinstance(preferred_scoring, list) else preferred_scoring,
            'notes': notes,
            'author': author
        }

        try:
            if override:
                # Update existing row for the team
                con.execute("""
                    UPDATE scouting.pit
                    SET height = ?,
                        weight = ?,
                        length = ?,
                        width = ?,
                        start_position = ?,
                        auto_route = ?,
                        scoring_capabilities = ?,
                        preferred_scoring = ?,
                        notes = ?,
                        author = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE team_number = ?
                """, [
                    data['height'], data['weight'], data['length'], data['width'],
                    data['start_position'], data['auto_route'], data['scoring_capabilities'],
                    data['preferred_scoring'], data['notes'], data['author'],
                    data['team_number']
                ])
                st.success("Data updated successfully!")
            else:
                # Insert new row for the team
                con.execute("""
                    INSERT INTO scouting.pit 
                    (team_number, height, weight, length, width, 
                    start_position, auto_route, scoring_capabilities, 
                    preferred_scoring, notes, author)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    data['team_number'], data['height'], data['weight'],
                    data['length'], data['width'], data['start_position'],
                    data['auto_route'], data['scoring_capabilities'],
                    data['preferred_scoring'], data['notes'], data['author']
                ])
                st.success("Data saved successfully!")
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
