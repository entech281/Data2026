import cachetools.func
import pandas as pd

from motherduck import con
import polars as pl

CACHE_SECONDS = 600

def get_matches_for_event(event_key:str) -> pd.DataFrame:
    all_matches = get_matches()
    return all_matches [ all_matches['event_key'] == event_key].sort_values(by=['time'], ascending=[True])


# Example controller to cache queries
# this will only run the query if it needs cache refresh
@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_matches() -> pl.DataFrame:
    return con.sql("select * from tba.matches").df();


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_rankings() -> pl.DataFrame:
    return con.sql("select * from tba.event_rankings").df();

@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_team_list(event_key:str) -> list:
    df = con.sql(f"""
            select red1, red2, red3, blue1, blue2, blue3
            from tba.matches
            where event_key = '{event_key }'
    """).df()
    unique_teams = pd.unique(df.values.ravel())
    return sorted(unique_teams.tolist())


def get_most_recent_event() -> str:
    all_events = get_event_list()
    if len(all_events) > 0:
        return all_events[0]
    else:
        return None


def get_event_list() -> pd.DataFrame:
    event_df = get_events()
    return event_df['event_key'].values.tolist()


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_events() -> pd.DataFrame:
    return con.sql("""
            select event_key, max(actual_time) from tba.matches 
            group by event_key
            order by max(actual_time) desc;    
    """).df()


@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def _get_tba_oprs_and_ranks() -> pd.DataFrame:
    tba_ranks =  con.sql("""
            select er.team_number, er.event_key,er.wins, er.losses, er.ties,er.rank,er.dq, op.oprs as opr, op.ccwms as ccwm, op.dprs as dpr
            from frc_2025.tba.event_rankings er
            join frc_2025.tba.oprs op on er.team_number = op.team_number and er.event_key = op.event_key
            order by er.rank asc;
    """).df()
    return tba_ranks


def get_tba_oprs_and_ranks_for_event(event_key:str) -> pd.DataFrame:
    r =  _get_tba_oprs_and_ranks()
    r = r[ r['event_key'] == event_key]
    return r

def get_oprs_and_ranks_for_event(event_key:str) -> pd.DataFrame:
    all_ranks = _get_tba_oprs_and_ranks()
    all_ranks_this_event = all_ranks[all_ranks['event_key'] == event_key]
    rank_summary_this_event = get_ranking_point_summary_for_event(event_key)
    return all_ranks_this_event.merge(rank_summary_this_event,on='team_number',how='inner')


def get_oprs_and_ranks_for_team(event_key:str, team_number: int) -> dict:
    all_ranks = get_oprs_and_ranks_for_event(event_key)
    filtered_for_team = all_ranks[ all_ranks['team_number'] == team_number]
    r = filtered_for_team.to_dict(orient='records')
    return r[0] if len(r) > 0 else {}


def get_robot_specific_data_from_matches( event_key:str) -> pd.DataFrame:
    # gets values out of the matches where we essentially DO have a value
    # per robot, per match
    d = []
    team_list = get_team_list(event_key)
    matches = get_matches_for_event(event_key)

    def _get_robot_specific_value(row, team_number: int, prefix: str, index: i )-> list:
        team_col = f"{prefix}{index}"
        suffix = f"robot{index}"
        if team_number in [row[team_col]]:
            return [{
                'team_number': row[team_number],
                'auto_line': row[f"red_auto_line_{suffix}"],
                'end_game': row[f"red_end_game_{suffix}"]
            }]
        else:
            return []

    for t in team_list:
        for _, row in matches.iterrows():
            d.extend(_get_robot_specific_value(row, t, 'red', 1 ))
            d.extend(_get_robot_specific_value(row, t, 'red', 2))
            d.extend(_get_robot_specific_value(row, t, 'red', 3))
            d.extend(_get_robot_specific_value(row, t, 'blue', 1 ))
            d.extend(_get_robot_specific_value(row, t, 'blue', 2))
            d.extend(_get_robot_specific_value(row, t, 'blue', 3))
    return pd.DataFrame(d)

@cachetools.func.ttl_cache(maxsize=128, ttl=CACHE_SECONDS)
def get_ranking_point_summary_for_event(event_key:str) -> pd.DataFrame:
    """
    This computes a summary of how many RPs each team has, and how they got them
    :param event_key:
    :return:
    """
    team_data = {}
    def get_team_summary(team_number:int):
        if team_number not in team_data:
            team_data[team_number] = {
                'team_number': team_number,
                'total_rp': 0,
                'auto_rp': 0,
                'win_rp': 0,
                'coral_rp': 0,
                'barge_rp': 0,
                'total_rp_sum': 0,
                'match_count': 0
            }
        return team_data[team_number]

    #there is probably a faster way to do this that's vectorized but
    #i dont want to figure it out right now
    matches = get_matches_for_event(event_key)
    matches = matches [ matches['comp_level'] == 'qm'] #only consider qualifiers for rankings


    def _add_team_rps_with_prefix(prefix:str,row):
        if prefix == "red":
            anti_prefix = "blue"
        else:
            anti_prefix = "red"

        for col in [f"{prefix}1", f"{prefix}2", f"{prefix}3"]:
            team_number = row[col]

            td = get_team_summary(team_number)

            # blue alliance calculated rp
            td['total_rp'] += row[f"{prefix}_rp"]
            td['match_count'] += 1
            # 3 for win, 1 for a tie
            our_score=row[f"{prefix}_score"]
            their_score=row[f"{anti_prefix}_score"]

            if our_score > their_score:
                td['win_rp'] += 3
            elif our_score == their_score:
                td['win_rp'] += 1

            if row[f'{prefix}_auto_bonus_achieved'] == 1:
                td['auto_rp'] += 1

            if row[f'{prefix}_coral_bonus_achieved'] == 1:
                td['coral_rp'] += 1

            if row[f'{prefix}_barge_bonus_achieved'] == 1:
                td['barge_rp'] += 1


    for _,row in matches.iterrows():
        _add_team_rps_with_prefix('red',row)
        _add_team_rps_with_prefix('blue', row)


    r = pd.DataFrame(team_data.values())
    r['avg_rp'] = r['total_rp'] / r['match_count']
    r['avg_win_rp'] = r['win_rp'] / r['match_count']
    r['avg_auto_rp'] = r['auto_rp'] / r['match_count']
    r['avg_coral_rp'] = r['coral_rp'] / r['match_count']
    r['avg_barge_rp'] = r['barge_rp'] / r['match_count']
    return r


def clear_caches():
    get_ranking_point_summary_for_event.cache_clear()
    _get_tba_oprs_and_ranks.cache_clear()
    get_matches.cache_clear()
    get_rankings.cache_clear()
    get_team_list.cache_clear()
    get_events.cache_clear()