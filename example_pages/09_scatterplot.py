import streamlit as st
import pandas as pd
import opr3
st.set_page_config(layout="wide")
df = opr3.latest_match() # Ensure your DataFrame has 'team_id' and z-score columns
df.reset_index(drop=True, inplace=True)
df['team_id'] = df['team_id'].apply(str)

st.title("Team Zscores")
st.caption("Select Characteristics to see z-scores for teams")
def get_all_characteristics():
    c = set(df.columns)
    c.remove('team_id')
    return list(c)

total_chars = [
    'their_score_z',
    'total_points_z',
    'rp_z',
    'margin_z',
    'score_z',
    'adjust_points_z',
]

penalty_chars = [
    'foul_points_z',
    'foul_count_z',
    'tech_foul_count_z',
]

auto_chars = [
    'auto_points_z',
    'auto_amp_note_count_z',
    'auto_leave_points_z',
    'auto_speaker_note_count_z',
    'auto_speaker_note_points_z',
    'auto_amp_note_points_z',
    'auto_total_note_points_z',
]

tele_chars = [
    'teleop_points_z',
    'teleop_speaker_note_count_z',
    'teleop_amp_note_count_z',
    'teleop_amp_note_points_z',
    'teleop_total_note_points_z',
    'teleop_speaker_note_amplified_points_z',
    'teleop_speaker_note_points_z',
    'teleop_speaker_note_amplified_count_z'
]

end_game_chars = [
    'end_game_note_in_trap_points_z',
    'end_game_spot_light_bonus_points_z',
    'end_game_on_stage_points_z',
    'end_game_harmony_points_z',
    'end_game_total_stage_points_z',
    'end_game_park_points_z',
]
selected_total_chars = st.pills("Match ",total_chars,selection_mode="multi")
selected_penalty_chars = st.pills("Penalties ",penalty_chars,selection_mode="multi")
selected_auto_chars = st.pills("Auto ",auto_chars,selection_mode="multi")
selected_tele_chars = st.pills("Tele ",tele_chars,selection_mode="multi")
selected_end_game_chars = st.pills("EndGame ",end_game_chars,selection_mode="multi")


selected_chars = selected_total_chars + selected_penalty_chars + selected_auto_chars +selected_tele_chars +selected_end_game_chars
#selected_chars = st.multiselect("Select Characteristics", get_all_characteristics(),key="selected_attribs")



cols = selected_chars + ['team_id']
df = df[cols]
all = pd.melt(df,id_vars=['team_id'],var_name='attribute',value_name='zscore')

st.scatter_chart(all, x='team_id',y='zscore',color='attribute',height=800)