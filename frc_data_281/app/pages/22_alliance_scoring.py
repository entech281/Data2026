import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from frc_data_281.app.components.event_selector import event_selector
from frc_data_281.db.cached_queries import (
    get_team_list,
    get_scouting_match_data,
    get_scouting_data_for_teams,
    get_next_unplayed_match,
    get_matches_for_event,
)

st.set_page_config(layout="wide")
st.title("Alliance Scoring Analysis")
st.caption("Compare scoring trends across alliances using FSC scouting data.")

selected_event = event_selector()

# --- Check for scouting data ---
scouting_df = get_scouting_match_data(selected_event)
if scouting_df.empty:
    st.warning("No FSC scouting data available for this event. Refresh data to sync from fscdata.org.")
    st.stop()

team_list = sorted(get_team_list(selected_event))
team_options = [int(t) for t in team_list]

# --- Alliance Setup ---
st.header("Alliance Setup")

# Auto-load from upcoming match
next_match = get_next_unplayed_match(selected_event)

col_load, col_match_pick = st.columns([1, 2])
with col_load:
    # Let user pick any qual match to load from
    matches_df = get_matches_for_event(selected_event)
    qual_matches = matches_df[matches_df['comp_level'] == 'qm'].sort_values('match_number')
    match_numbers = qual_matches['match_number'].astype(int).tolist()

    default_match_idx = 0
    if next_match and next_match['match_number'] in match_numbers:
        default_match_idx = match_numbers.index(next_match['match_number'])

    load_match = st.selectbox(
        "Load teams from match",
        options=match_numbers,
        index=default_match_idx if match_numbers else 0,
        format_func=lambda m: f"Qual {m}" + (" (next)" if next_match and m == next_match['match_number'] else ""),
    ) if match_numbers else None

# Get teams from selected match
match_teams = None
if load_match is not None:
    match_row = qual_matches[qual_matches['match_number'] == load_match]
    if not match_row.empty:
        row = match_row.iloc[0]
        match_teams = {
            'red': [int(row['red1']), int(row['red2']), int(row['red3'])],
            'blue': [int(row['blue1']), int(row['blue2']), int(row['blue3'])],
        }


def _team_index(team_val, options):
    """Get index for a team in the options list, or 0 if not found."""
    try:
        return options.index(int(team_val))
    except (ValueError, TypeError):
        return 0


# Red and Blue alliance selectors side-by-side
col_red, col_blue = st.columns(2)

with col_red:
    st.subheader("🔴 Red Alliance")
    red1 = st.selectbox(
        "Red 1", team_options, key="red1",
        index=_team_index(match_teams['red'][0], team_options) if match_teams else 0,
        format_func=lambda t: str(t),
    )
    red2 = st.selectbox(
        "Red 2", team_options, key="red2",
        index=_team_index(match_teams['red'][1], team_options) if match_teams else min(1, len(team_options) - 1),
        format_func=lambda t: str(t),
    )
    red3 = st.selectbox(
        "Red 3", team_options, key="red3",
        index=_team_index(match_teams['red'][2], team_options) if match_teams else min(2, len(team_options) - 1),
        format_func=lambda t: str(t),
    )

with col_blue:
    st.subheader("🔵 Blue Alliance")
    blue1 = st.selectbox(
        "Blue 1", team_options, key="blue1",
        index=_team_index(match_teams['blue'][0], team_options) if match_teams else min(3, len(team_options) - 1),
        format_func=lambda t: str(t),
    )
    blue2 = st.selectbox(
        "Blue 2", team_options, key="blue2",
        index=_team_index(match_teams['blue'][1], team_options) if match_teams else min(4, len(team_options) - 1),
        format_func=lambda t: str(t),
    )
    blue3 = st.selectbox(
        "Blue 3", team_options, key="blue3",
        index=_team_index(match_teams['blue'][2], team_options) if match_teams else min(5, len(team_options) - 1),
        format_func=lambda t: str(t),
    )

red_teams = [red1, red2, red3]
blue_teams = [blue1, blue2, blue3]
all_selected = red_teams + blue_teams

# --- Get scouting data for selected teams ---
alliance_data = get_scouting_data_for_teams(selected_event, all_selected)

if alliance_data.empty:
    st.warning("No scouting data found for the selected teams at this event.")
    st.stop()

st.divider()

# --- Scoring Line Plots ---
st.header("Scoring Trends")

# Color palettes for each alliance
RED_COLORS = ["#e74c3c", "#c0392b", "#ff6b6b"]
BLUE_COLORS = ["#3498db", "#2980b9", "#74b9ff"]


def _build_team_traces(df: pd.DataFrame, teams: list[int], colors: list[str],
                       y_col: str, dash: str = "solid") -> list:
    """Build Plotly scatter traces for a list of teams."""
    traces = []
    for i, team in enumerate(teams):
        team_df = df[df['team_number'] == team].sort_values('match_number')
        if team_df.empty:
            continue
        traces.append(go.Scatter(
            x=team_df['match_number'],
            y=team_df[y_col],
            mode='lines+markers',
            name=f"{team}",
            line=dict(color=colors[i % len(colors)], dash=dash, width=2),
            marker=dict(size=6),
            hovertemplate=f"Team {team}<br>Match %{{x}}<br>{y_col}: %{{y}}<extra></extra>",
        ))
    return traces


def _build_alliance_total_trace(df: pd.DataFrame, teams: list[int], y_col: str,
                                color: str, name: str) -> go.Scatter | None:
    """Build a trace showing the alliance total (sum of all 3 teams) per match."""
    team_df = df[df['team_number'].isin(teams)]
    if team_df.empty:
        return None
    totals = team_df.groupby('match_number')[y_col].sum().reset_index()
    totals = totals.sort_values('match_number')
    return go.Scatter(
        x=totals['match_number'],
        y=totals[y_col],
        mode='lines+markers',
        name=name,
        line=dict(color=color, width=3),
        marker=dict(size=8),
        hovertemplate=f"{name}<br>Match %{{x}}<br>Total: %{{y}}<extra></extra>",
    )


# Chart configurations
SCORING_CHARTS = [
    ("Auto Fuel Score", "auto_fuel_score"),
    ("Teleop Fuel Score", "teleop_fuel_score"),
    ("Alliance Human Fuel", "alliance_human_fuel"),
]

# Add total fuel as a computed column
alliance_data = alliance_data.copy()
alliance_data['total_fuel'] = (
    alliance_data['auto_fuel_score'].fillna(0) +
    alliance_data['teleop_fuel_score'].fillna(0)
)
SCORING_CHARTS.append(("Total Fuel (Auto + Teleop)", "total_fuel"))

chart_selection = st.pills(
    "Scoring Category",
    [c[0] for c in SCORING_CHARTS],
    default="Total Fuel (Auto + Teleop)",
    selection_mode="single",
)

if chart_selection:
    y_col = next(c[1] for c in SCORING_CHARTS if c[0] == chart_selection)

    # Per-team traces
    fig = go.Figure()
    for trace in _build_team_traces(alliance_data, red_teams, RED_COLORS, y_col):
        fig.add_trace(trace)
    for trace in _build_team_traces(alliance_data, blue_teams, BLUE_COLORS, y_col, dash="dash"):
        fig.add_trace(trace)

    fig.update_layout(
        title=f"{chart_selection} by Team Over Qualification Matches",
        xaxis_title="Qualification Match Number",
        yaxis_title=chart_selection,
        hovermode="x unified",
        legend_title="Team",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Alliance totals chart
    st.subheader("Alliance Totals")
    fig_totals = go.Figure()
    red_total = _build_alliance_total_trace(alliance_data, red_teams, y_col, "#e74c3c", "Red Alliance")
    blue_total = _build_alliance_total_trace(alliance_data, blue_teams, y_col, "#3498db", "Blue Alliance")
    if red_total:
        fig_totals.add_trace(red_total)
    if blue_total:
        fig_totals.add_trace(blue_total)

    fig_totals.update_layout(
        title=f"Alliance Total {chart_selection}",
        xaxis_title="Qualification Match Number",
        yaxis_title=f"Total {chart_selection}",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig_totals, use_container_width=True)

st.divider()

# --- Summary Stats ---
st.header("Summary Statistics")


def _team_summary(df: pd.DataFrame, team: int) -> dict:
    """Compute summary stats for a single team."""
    td = df[df['team_number'] == team]
    if td.empty:
        return {
            'team_number': team, 'matches_scouted': 0,
            'avg_auto_fuel': None, 'avg_teleop_fuel': None, 'avg_total_fuel': None,
            'climb_attempt_rate': None, 'climb_success_rate': None,
            'pct_active_scored': None, 'pct_active_defense': None,
        }
    n = len(td)
    climb_attempts = td['endgame_climb_try'].sum() if 'endgame_climb_try' in td.columns else 0
    climb_success = td['endgame_climb_level'].notna() & (td['endgame_climb_level'] != 'None') & (td['endgame_climb_level'] != 'nan')
    return {
        'team_number': team,
        'matches_scouted': n,
        'avg_auto_fuel': td['auto_fuel_score'].mean() if 'auto_fuel_score' in td.columns else None,
        'avg_teleop_fuel': td['teleop_fuel_score'].mean() if 'teleop_fuel_score' in td.columns else None,
        'avg_total_fuel': td['total_fuel'].mean() if 'total_fuel' in td.columns else None,
        'climb_attempt_rate': (climb_attempts / n * 100) if n > 0 else None,
        'climb_success_rate': (climb_success.sum() / n * 100) if n > 0 else None,
        'pct_active_scored': (td['strategy_active_scored'].sum() / n * 100) if 'strategy_active_scored' in td.columns and n > 0 else None,
        'pct_active_defense': (td['strategy_active_defense'].sum() / n * 100) if 'strategy_active_defense' in td.columns and n > 0 else None,
    }


col_red_stats, col_blue_stats = st.columns(2)

with col_red_stats:
    st.subheader("🔴 Red Alliance")
    red_summaries = pd.DataFrame([_team_summary(alliance_data, t) for t in red_teams])
    st.dataframe(
        red_summaries.style.format({
            'avg_auto_fuel': '{:.1f}', 'avg_teleop_fuel': '{:.1f}', 'avg_total_fuel': '{:.1f}',
            'climb_attempt_rate': '{:.0f}%', 'climb_success_rate': '{:.0f}%',
            'pct_active_scored': '{:.0f}%', 'pct_active_defense': '{:.0f}%',
        }, na_rep="—"),
        hide_index=True, use_container_width=True,
    )

with col_blue_stats:
    st.subheader("🔵 Blue Alliance")
    blue_summaries = pd.DataFrame([_team_summary(alliance_data, t) for t in blue_teams])
    st.dataframe(
        blue_summaries.style.format({
            'avg_auto_fuel': '{:.1f}', 'avg_teleop_fuel': '{:.1f}', 'avg_total_fuel': '{:.1f}',
            'climb_attempt_rate': '{:.0f}%', 'climb_success_rate': '{:.0f}%',
            'pct_active_scored': '{:.0f}%', 'pct_active_defense': '{:.0f}%',
        }, na_rep="—"),
        hide_index=True, use_container_width=True,
    )

# Alliance combined potential
st.subheader("Combined Alliance Scoring Potential")
col_r, col_b = st.columns(2)

with col_r:
    red_avg = red_summaries['avg_total_fuel'].sum()
    st.metric("🔴 Red Alliance Avg Total Fuel", f"{red_avg:.1f}" if pd.notna(red_avg) else "—")

with col_b:
    blue_avg = blue_summaries['avg_total_fuel'].sum()
    st.metric("🔵 Blue Alliance Avg Total Fuel", f"{blue_avg:.1f}" if pd.notna(blue_avg) else "—")
