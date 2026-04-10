import streamlit as st
import pandas as pd
from tabulate import tabulate

from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.db import cached_queries as cached_data
from frc_data_281.db.connection import get_connection
from frc_data_281.analysis import opr as opr3


def _df_to_md_table(df: pd.DataFrame, float_fmt=".2f") -> str:
    """Convert a DataFrame to a Markdown pipe table, intelligently formatting integers vs floats."""
    if df.empty:
        return "_No data available._\n"

    # Columns that should be formatted as integers
    integer_column_names = {
        'team_number', 'team_id', 'team', 'rank', 'wins', 'losses', 'ties', 'dq',
        'match_count', 'total_rp', 'win_rp', 'energized_rp', 'supercharged_rp', 'traversal_rp',
        'auto_rp', 'coral_rp', 'barge_rp', 'match_number',
        'red1', 'red2', 'red3', 'blue1', 'blue2', 'blue3',
        'red_score', 'blue_score'
    }

    # Format columns before passing to tabulate
    df_formatted = df.copy()
    for col in df_formatted.columns:
        is_int_dtype = pd.api.types.is_integer_dtype(df_formatted[col])
        is_int_by_name = col.lower() in integer_column_names
        
        if (is_int_dtype or is_int_by_name) and pd.api.types.is_numeric_dtype(df_formatted[col]):
            # Format as integer (no decimals)
            df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x)}" if pd.notna(x) else "")

    return tabulate(df_formatted, headers="keys", tablefmt="pipe", showindex=False) + "\n"


def _build_event_overview(event_key: str, team_list: list, matches: pd.DataFrame) -> str:
    played = matches[matches["winning_alliance"].notna() & (matches["winning_alliance"] != "")]
    return "\n".join([
        f"# FRC Scouting Report — {event_key}\n",
        "## Event Overview\n",
        f"- **Event Key:** {event_key}",
        f"- **Number of Teams:** {len(team_list)}",
        f"- **Total Matches Scheduled:** {len(matches)}",
        f"- **Matches Played:** {len(played)}",
        "",
    ])


def _build_rankings_section(event_key: str) -> str:
    rankings = cached_data.get_oprs_and_ranks_for_event(event_key)
    if rankings.empty:
        return "## Rankings & OPR Summary\n\n_No ranking data available._\n\n"

    season = int(event_key[:4])
    if season >= 2026:
        bonus_cols = ['avg_energized_rp', 'avg_supercharged_rp', 'avg_traversal_rp']
    else:
        bonus_cols = ['avg_auto_rp', 'avg_coral_rp', 'avg_barge_rp']

    display_cols = ['team_number', 'rank', 'wins', 'losses', 'ties', 'opr', 'dpr', 'ccwm',
                    'total_rp', 'avg_rp', 'avg_win_rp'] + bonus_cols
    display_cols = [c for c in display_cols if c in rankings.columns]
    rankings = rankings[display_cols].sort_values('rank')

    return "\n".join([
        "## Rankings & OPR Summary\n",
        "Each team's event ranking with Offensive Power Rating (OPR), "
        "Defensive Power Rating (DPR), and Calculated Contribution to Winning Margin (CCWM). "
        "Higher OPR = stronger scoring. Lower DPR = better defense (fewer points allowed). "
        "CCWM measures overall contribution to alliance win margin.\n",
        _df_to_md_table(rankings),
        "",
    ])


def _build_rp_section(event_key: str) -> str:
    rp_summary = cached_data.get_ranking_point_summary_for_event(event_key)
    if rp_summary.empty:
        return "## Ranking Point Breakdown\n\n_No RP data available._\n\n"

    season = int(event_key[:4])
    if season >= 2026:
        bonus_cols = ['energized_rp', 'supercharged_rp', 'traversal_rp',
                      'avg_energized_rp', 'avg_supercharged_rp', 'avg_traversal_rp']
    else:
        bonus_cols = ['auto_rp', 'coral_rp', 'barge_rp',
                      'avg_auto_rp', 'avg_coral_rp', 'avg_barge_rp']

    display_cols = ['team_number', 'match_count', 'total_rp', 'avg_rp',
                    'win_rp', 'avg_win_rp'] + bonus_cols
    display_cols = [c for c in display_cols if c in rp_summary.columns]
    rp_summary = rp_summary[display_cols].sort_values('total_rp', ascending=False)

    return "\n".join([
        "## Ranking Point Breakdown\n",
        "How each team earned their ranking points. "
        "Win RP: 3 for a win, 1 for a tie. "
        "Bonus RPs are earned by achieving specific game objectives with the alliance.\n",
        _df_to_md_table(rp_summary),
        "",
    ])


def _build_ccm_section(event_key: str) -> str:
    try:
        ccm = opr3.get_ccm_data_for_event(event_key)
        non_z = opr3.select_non_zscore_columns(ccm)
    except Exception:
        return "## Component Contribution Metrics\n\n_No CCM data available._\n\n"

    if non_z.empty:
        return "## Component Contribution Metrics\n\n_No CCM data available._\n\n"

    non_z = non_z.drop(columns=['event_key'], errors='ignore')
    if 'team_id' in non_z.columns:
        non_z = non_z.rename(columns={'team_id': 'team_number'})
    if 'score' in non_z.columns:
        non_z = non_z.sort_values('score', ascending=False)

    return "\n".join([
        "## Component Contribution Metrics (CCM)\n",
        "CCM breaks down OPR into individual game components using matrix regression. "
        "Each value represents how many points a team contributes in that game element. "
        "Use this to identify specific strengths (e.g., strong auto, good hub scoring, consistent climbing).\n",
        _df_to_md_table(non_z),
        "",
    ])


def _build_zscore_section(event_key: str) -> str:
    try:
        z_df, _ = opr3.get_ccm_data_for_event_separated(event_key)
    except Exception:
        return "## Z-Score Analysis\n\n_No z-score data available._\n\n"

    if z_df.empty:
        return "## Z-Score Analysis\n\n_No z-score data available._\n\n"

    if 'team_id' in z_df.columns:
        z_df = z_df.rename(columns={'team_id': 'team_number'})

    # Drop noisy/granular columns
    cols_to_drop = [c for c in z_df.columns if
                    'g206_penalty' in c or
                    any(f'shift{i}' in c for i in range(1, 5))]
    z_df = z_df.drop(columns=cols_to_drop, errors='ignore')

    return "\n".join([
        "## Z-Score Analysis\n",
        "Z-scores compare each team to the event average. "
        "0 = average, positive = above average, negative = below average. "
        "Values above 1.5 or below -1.5 are notably strong or weak; above 2.0 is exceptional.\n",
        "**Note:** Z-scores for foul and opponent metrics (foul count, foul points, tech foul count, "
        "opponent score, opponent RP) have been **negated** so that positive values always mean "
        "\"good\" (fewer fouls, lower opponent score) and negative values always mean \"bad\" "
        "(more fouls, higher opponent score).\n",
        _df_to_md_table(z_df),
        "",
    ])


def _build_pit_scouting_section(team_list: list) -> str:
    try:
        with get_connection() as con:
            pit = con.sql("SELECT * FROM scouting.pit").df()
    except Exception:
        return "## Pit Scouting Data\n\n_No pit scouting data available._\n\n"

    if pit.empty:
        return "## Pit Scouting Data\n\n_No pit scouting data available._\n\n"

    if 'team_number' in pit.columns:
        pit = pit[pit['team_number'].isin(team_list)]
    if pit.empty:
        return "## Pit Scouting Data\n\n_No pit scouting data for teams at this event._\n\n"

    # Drop BLOBs and timestamps — not useful for LLM
    pit = pit.drop(columns=[c for c in ['auto_route', 'robot_photo', 'created_at']
                            if c in pit.columns], errors='ignore')

    lines = [
        "## Pit Scouting Data\n",
        "Collected by scouts visiting each team's pit. "
        "Includes robot dimensions, scoring capabilities, and scout observations.\n",
    ]
    for _, row in pit.iterrows():
        team = row.get('team_number', 'Unknown')
        lines.append(f"### Team {team}\n")
        for col in pit.columns:
            if col == 'team_number':
                continue
            val = row[col]
            if pd.notna(val) and val != '' and val != 0:
                label = col.replace('_', ' ').title()
                lines.append(f"- **{label}:** {val}")
        lines.append("")

    return "\n".join(lines)


def _build_tags_section(team_list: list) -> str:
    try:
        with get_connection() as con:
            tags = con.sql("SELECT * FROM scouting.tags").df()
    except Exception:
        return "## Team Tags\n\n_No team tags available._\n\n"

    if tags.empty:
        return "## Team Tags\n\n_No team tags have been recorded._\n\n"

    if 'team_number' in tags.columns:
        tags = tags[tags['team_number'].isin(team_list)]
    if tags.empty:
        return "## Team Tags\n\n_No tags for teams at this event._\n\n"

    tags = tags.drop(columns=[c for c in ['mod_dte'] if c in tags.columns], errors='ignore')

    return "\n".join([
        "## Team Tags\n",
        "Quick labels assigned by scouts capturing notable traits about a team's robot or driving.\n",
        _df_to_md_table(tags, float_fmt=".0f"),
        "",
    ])


def _build_match_results_section(matches: pd.DataFrame) -> str:
    played = matches[matches["winning_alliance"].notna() & (matches["winning_alliance"] != "")]
    if played.empty:
        return "## Match Results\n\n_No completed matches._\n\n"

    display_cols = ['key', 'comp_level', 'match_number',
                    'red1', 'red2', 'red3', 'red_score',
                    'blue1', 'blue2', 'blue3', 'blue_score',
                    'winning_alliance']
    display_cols = [c for c in display_cols if c in played.columns]
    played = played[display_cols].sort_values('match_number')

    return "\n".join([
        "## Match Results\n",
        "All completed matches with alliance lineups and scores. "
        "Each row shows the three teams on each alliance (red and blue) and the final score.\n",
        _df_to_md_table(played, float_fmt=".0f"),
        "",
    ])


# --- Streamlit Page ---

st.set_page_config(layout="wide")
st.title("NotebookLM Export")
st.caption("Download a comprehensive Markdown file of event data for use with NotebookLM.")

selected_event = event_selector()

with st.spinner("Gathering event data..."):
    team_list = cached_data.get_team_list(selected_event)
    matches = cached_data.get_matches_for_event(selected_event)

    sections = [
        _build_event_overview(selected_event, team_list, matches),
        _build_rankings_section(selected_event),
        _build_rp_section(selected_event),
        _build_ccm_section(selected_event),
        _build_zscore_section(selected_event),
        _build_pit_scouting_section(team_list),
        _build_tags_section(team_list),
        _build_match_results_section(matches),
    ]

    md_content = "\n".join(sections)

filename = f"{selected_event}_scouting_data.md"

st.download_button(
    label=f"⬇️ Download {filename}",
    data=md_content,
    file_name=filename,
    mime="text/markdown",
)

with st.expander("Preview Export", expanded=False):
    st.markdown(md_content)
