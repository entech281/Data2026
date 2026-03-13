import cachetools.func
import pandas as pd

from frc_data_281.db.connection import get_connection
from frc_data_281.the_blue_alliance.client import DISTRICT_EVENTS, get_teams_for_event, team_number_from_key
import polars as pl

CACHE_SECONDS = 600


def get_matches_for_event(event_key: str) -> pd.DataFrame:
    """Get all matches for a specific event, sorted by time.

    Args:
        event_key: Event key identifier (e.g., '2025week0').

    Returns:
        DataFrame containing match data for the specified event.
    """
    all_matches = get_matches()
    return all_matches[all_matches['event_key'] == event_key].sort_values(by=['time'], ascending=[True])


# Example controller to cache queries
# this will only run the query if it needs cache refresh
@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_matches() -> pl.DataFrame:
    """Get all matches from the database.

    Returns:
        DataFrame containing all match data.
    """
    with get_connection() as con:
        return con.sql("select * from tba.matches").df()


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_rankings() -> pl.DataFrame:
    """Get all event rankings from the database.

    Returns:
        DataFrame containing event rankings data.
    """
    with get_connection() as con:
        return con.sql("select * from tba.event_rankings").df()


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_team_list(event_key: str) -> list:
    """Get sorted list of all teams participating in an event.
    
    First tries to get teams from match data (fast). If no matches exist yet,
    fetches from TBA API directly (for events that haven't started).

    Args:
        event_key: Event key identifier (e.g., '2025week0').

    Returns:
        Sorted list of team numbers.
    """
    # Try to get teams from matches first
    with get_connection() as con:
        df = con.sql(f"""
                select red1, red2, red3, blue1, blue2, blue3
                from tba.matches
                where event_key = '{event_key}'
        """).df()
    
    if not df.empty:
        unique_teams = pd.unique(df.values.ravel())
        return sorted(unique_teams.tolist())
    
    # Fallback: fetch teams from TBA API (for events without match data yet)
    try:
        tba_teams = get_teams_for_event(event_key)
        if tba_teams:
            team_numbers = [team_number_from_key(t['key']) for t in tba_teams]
            return sorted(team_numbers)
    except Exception:
        pass
    
    return []


def get_most_recent_event() -> str:
    """Get the most recent event key based on match times.

    Returns:
        Event key of the most recent event, or None if no events exist.
    """
    all_events = get_event_list()
    if len(all_events) > 0:
        return all_events[0]
    else:
        return None


def get_event_list() -> pd.DataFrame:
    """Get list of all event keys, ordered by most recent first.

    Returns:
        List of event key strings.
    """
    event_df = get_events()
    return event_df['event_key'].values.tolist()


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_events() -> pd.DataFrame:
    """Get all events with their most recent match times.
    
    Includes all configured district events, even if they have no matches yet.

    Returns:
        DataFrame with event keys and their most recent match times.
    """
    with get_connection() as con:
        # Get events that have matches
        df = con.sql("""
                select event_key, max(actual_time) as actual_time from tba.matches
                group by event_key
                order by max(actual_time) desc;
        """).df()
    
    # Ensure all configured events are in the list, even without match data
    events_in_db = set(df['event_key'].tolist())
    configured_events = set(DISTRICT_EVENTS)
    missing_events = configured_events - events_in_db
    
    if missing_events:
        # Add missing configured events with null actual_time (they'll sort to the end)
        missing_df = pd.DataFrame({
            'event_key': list(missing_events),
            'actual_time': [None] * len(missing_events)
        })
        df = pd.concat([df, missing_df], ignore_index=True)
        # Re-sort: events with match data by actual_time desc, then missing events
        df = df.sort_values('actual_time', ascending=False, na_position='last')
    
    return df


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def _get_tba_oprs_and_ranks() -> pd.DataFrame:
    """Get OPR, CCWM, DPR and rankings from The Blue Alliance data.

    Returns:
        DataFrame with team rankings and calculated metrics.
    """
    with get_connection() as con:
        tba_ranks = con.sql("""
                select er.team_number, er.event_key,er.wins, er.losses, er.ties,er.rank,er.dq, op.oprs as opr, op.ccwms as ccwm, op.dprs as dpr
                from tba.event_rankings er
                join tba.oprs op on er.team_number = op.team_number and er.event_key = op.event_key
                order by er.rank asc;
        """).df()
    return tba_ranks


def get_tba_oprs_and_ranks_for_event(event_key: str) -> pd.DataFrame:
    """Get TBA OPR and rankings for a specific event.

    Args:
        event_key: Event key identifier (e.g., '2025week0').

    Returns:
        DataFrame with OPR and ranking data for the event.
    """
    r = _get_tba_oprs_and_ranks()
    r = r[r['event_key'] == event_key]
    return r


def get_oprs_and_ranks_for_event(event_key: str) -> pd.DataFrame:
    """Get combined OPR, rankings, and ranking point summary for an event.

    Args:
        event_key: Event key identifier (e.g., '2025week0').

    Returns:
        DataFrame with OPR, rankings, and RP summary merged.
    """
    all_ranks = _get_tba_oprs_and_ranks()
    all_ranks_this_event = all_ranks[all_ranks['event_key'] == event_key]
    rank_summary_this_event = get_ranking_point_summary_for_event(event_key)
    return all_ranks_this_event.merge(rank_summary_this_event, on='team_number', how='inner')


def get_oprs_and_ranks_for_team(event_key: str, team_number: int) -> dict:
    """Get OPR and ranking data for a specific team at an event.

    Args:
        event_key: Event key identifier (e.g., '2025week0').
        team_number: Team number.

    Returns:
        Dictionary with team's OPR and ranking data, or empty dict if not found.
    """
    all_ranks = get_oprs_and_ranks_for_event(event_key)
    filtered_for_team = all_ranks[all_ranks['team_number'] == team_number]
    r = filtered_for_team.to_dict(orient='records')
    return r[0] if len(r) > 0 else {}


def get_robot_specific_data_from_matches(event_key: str) -> pd.DataFrame:
    """Get robot-specific data from matches (data tracked per robot, not per alliance).

    Args:
        event_key: Event key identifier (e.g., '2026sccha').

    Returns:
        DataFrame with robot-specific match data.
    """
    season = int(event_key[:4])
    d = []
    team_list = get_team_list(event_key)
    matches = get_matches_for_event(event_key)

    if season >= 2026:
        auto_col = "auto_tower"
        endgame_col = "end_game_tower"
    else:
        auto_col = "auto_line"
        endgame_col = "end_game"

    def _get_robot_specific_value(row, team_number: int, prefix: str, index: int) -> list:
        team_col = f"{prefix}{index}"
        suffix = f"robot{index}"
        if team_number in [row[team_col]]:
            auto_field = f"{prefix}_{auto_col}_{suffix}"
            endgame_field = f"{prefix}_{endgame_col}_{suffix}"
            return [{
                'team_number': team_number,
                'auto_action': row.get(auto_field),
                'end_game': row.get(endgame_field),
            }]
        else:
            return []

    for t in team_list:
        for _, row in matches.iterrows():
            d.extend(_get_robot_specific_value(row, t, 'red', 1))
            d.extend(_get_robot_specific_value(row, t, 'red', 2))
            d.extend(_get_robot_specific_value(row, t, 'red', 3))
            d.extend(_get_robot_specific_value(row, t, 'blue', 1))
            d.extend(_get_robot_specific_value(row, t, 'blue', 2))
            d.extend(_get_robot_specific_value(row, t, 'blue', 3))
    return pd.DataFrame(d)


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_ranking_point_summary_for_event(event_key: str) -> pd.DataFrame:
    """
    Compute a summary of how many RPs each team has earned, and how they got them.

    Season-aware: adapts RP bonus columns for 2025 vs 2026+ games.
    - 2025: auto_bonus_achieved, coral_bonus_achieved, barge_bonus_achieved
    - 2026: energized_achieved, supercharged_achieved, traversal_achieved

    :param event_key:
    :return:
    """
    season = int(event_key[:4])
    team_data = {}

    if season >= 2026:
        bonus_keys = ['energized', 'supercharged', 'traversal']
        bonus_cols = {
            'energized': 'TEAM_energized_achieved',
            'supercharged': 'TEAM_supercharged_achieved',
            'traversal': 'TEAM_traversal_achieved',
        }
    else:
        bonus_keys = ['auto', 'coral', 'barge']
        bonus_cols = {
            'auto': 'TEAM_auto_bonus_achieved',
            'coral': 'TEAM_coral_bonus_achieved',
            'barge': 'TEAM_barge_bonus_achieved',
        }

    def get_team_summary(team_number: int):
        if team_number not in team_data:
            entry = {
                'team_number': team_number,
                'total_rp': 0,
                'win_rp': 0,
                'match_count': 0,
            }
            for key in bonus_keys:
                entry[f'{key}_rp'] = 0
            team_data[team_number] = entry
        return team_data[team_number]

    matches = get_matches_for_event(event_key)
    matches = matches[matches['comp_level'] == 'qm']
    matches = matches[matches['red_score'].notna() & matches['blue_score'].notna()]

    def _add_team_rps_with_prefix(prefix: str, row):
        anti_prefix = 'blue' if prefix == 'red' else 'red'

        for col in [f"{prefix}1", f"{prefix}2", f"{prefix}3"]:
            team_number = row[col]
            td = get_team_summary(team_number)

            td['total_rp'] += row[f"{prefix}_rp"]
            td['match_count'] += 1

            our_score = row[f"{prefix}_score"]
            their_score = row[f"{anti_prefix}_score"]
            if our_score > their_score:
                td['win_rp'] += 3
            elif our_score == their_score:
                td['win_rp'] += 1

            for key, col_template in bonus_cols.items():
                bonus_col = col_template.replace('TEAM', prefix)
                if bonus_col in row and row[bonus_col] is not pd.NA and row[bonus_col] == 1:
                    td[f'{key}_rp'] += 1

    for _, row in matches.iterrows():
        _add_team_rps_with_prefix('red', row)
        _add_team_rps_with_prefix('blue', row)

    r = pd.DataFrame(team_data.values())
    r['avg_rp'] = r['total_rp'] / r['match_count']
    r['avg_win_rp'] = r['win_rp'] / r['match_count']
    for key in bonus_keys:
        r[f'avg_{key}_rp'] = r[f'{key}_rp'] / r['match_count']
    return r


def clear_caches():
    get_ranking_point_summary_for_event.cache_clear()
    _get_tba_oprs_and_ranks.cache_clear()
    get_matches.cache_clear()
    get_rankings.cache_clear()
    get_team_list.cache_clear()
    get_events.cache_clear()
