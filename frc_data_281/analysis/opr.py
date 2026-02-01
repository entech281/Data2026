import pandas as pd

from frc_data_281.analysis.season_specific.season_2025 import (
    aggregate_reef_scoring,
    add_scoring_computations,
)
from frc_data_281.db import cached_queries as cached_data
import numpy as np
from scipy.stats import zscore
import cachetools.func
from frc_data_281.analysis.dataset_tools import (
    drop_columns_with_word_in_column_name,
    find_columns_with_suffix,
    remove_from_list
)
from tabulate import tabulate

CCM_CACHE_SECONDS = 60


def column_map_for_color(columns: list, color: str) -> tuple[dict[str, str], list[str]]:
    column_map = {
        color + "1": "t1",
        color + "2": "t2",
        color + "3": "t3",
    }
    automapped_fields = set()
    if color == "red":
        column_map["blue_score"] = "their_score"
        column_map["blue_rp"] = "their_rp"

    if color == "blue":
        column_map["red_score"] = "their_score"
        column_map["red_rp"] = "their_rp"

    color_prefix = color + "_"
    # get columns associated with this team, like team_<value>
    for c in columns:
        if c.startswith(color_prefix):
            computed_field = c.replace(color_prefix, "")
            automapped_fields.add(computed_field)
            column_map[c] = computed_field

    return column_map, list(automapped_fields)


def _calculate_opr_ccwm_dpr(matches: pd.DataFrame) -> pd.DataFrame:
    # get the unique list of teams
    team_list = pd.unique(matches[['red1', 'red2', 'red3', 'blue1', 'blue2', 'blue3']].values.ravel('K'))

    # let's only consider numeric columns for now. later we can add converters for booleans and strings
    numeric_columns = matches.select_dtypes(include='number').columns
    red_col_map, automapped_fields = column_map_for_color(numeric_columns, 'red')
    blue_col_map, automapped_fields = column_map_for_color(numeric_columns, 'blue')

    red_data = matches.rename(columns=red_col_map)
    blue_data = matches.rename(columns=blue_col_map)

    all_data = pd.concat([red_data, blue_data])
    all_data['margin'] = all_data['score'] - all_data['their_score']

    m = []
    for idx, match in all_data.iterrows():
        r = []
        for team in team_list:
            if match['t1'] == team or match['t2'] == team or match['t3'] == team:
                r.append(1)
            else:
                r.append(0)
        m.append(r)
    m_m = np.matrix(m)

    # left side values are all the columns in the map, MINUS a key few
    computed_cols = ['margin', 'their_score'] + automapped_fields

    left_side = all_data[computed_cols]
    c_c = np.matrix(left_side)

    pseudo_inverse = np.linalg.pinv(m_m)
    computed = np.matmul(pseudo_inverse, c_c)

    results_2 = pd.DataFrame(computed, columns=computed_cols)
    teams_2 = pd.DataFrame(team_list, columns=['team_id'])
    results_all = pd.concat([teams_2, results_2], axis=1)

    return results_all.sort_values(by=['score'], ascending=False)


def add_zscores(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    new_df = df.copy()
    for c in cols:
        try:
            # Convert to numeric, coercing errors to NaN
            values = pd.to_numeric(df[c], errors='coerce')
            # Convert to float64 numpy array
            values_array = values.astype(np.float64).to_numpy()
            # Use scipy's zscore with nan_policy to handle NaN values
            new_df[c + "_z"] = zscore(values_array, nan_policy='omit')
        except Exception as e:
            # If zscore fails, skip this column
            print(f"Warning: Could not compute z-score for column '{c}': {e}")
            new_df[c + "_z"] = np.nan
    return new_df


def analyze_ccm(df: pd.DataFrame) -> pd.DataFrame:
    matches = df
    r = _calculate_opr_ccwm_dpr(matches)
    r = drop_columns_with_word_in_column_name(r, 'threshold')  # robot1,2, 3 are robot specific, we can get those later
    r = drop_columns_with_word_in_column_name(r, '_robot')
    cols_to_use = remove_from_list(r.columns, ['team_id'])
    with_z = add_zscores(r, cols_to_use)
    return with_z



def select_z_score_columns(df: pd.DataFrame, other_columns=[]):
    weighted_columns = find_columns_with_suffix(df, "_z") + other_columns
    return df[weighted_columns]


def select_non_zscore_columns(df: pd.DataFrame):
    zscore_columns = find_columns_with_suffix(df, "_z")
    return df.drop(columns=zscore_columns)


def apply_season_specific_treatment(event_data: pd.DataFrame, season: int) -> pd.DataFrame:
    """Apply season-specific data treatment to event data.

    Args:
        event_data: DataFrame containing match data for an event
        season: The season year (e.g., 2025)

    Returns:
        DataFrame with season-specific transformations applied
    """
    if season == 2025:
        event_data = aggregate_reef_scoring(event_data)
        event_data = add_scoring_computations(event_data)

    return event_data


@cachetools.func.ttl_cache(maxsize=128, ttl=CCM_CACHE_SECONDS)
def get_ccm_data() -> pd.DataFrame:
    print("This is the new version of get_ccm_data")
    all_match_data = cached_data.get_matches()
    print(f"Before Filter {len(all_match_data)}")
    all_match_data = all_match_data[all_match_data["winning_alliance"].notna()]
    all_match_data = all_match_data[all_match_data["winning_alliance"] != '']
    print(f"After Filter {len(all_match_data)}")
    event_keys = all_match_data['event_key'].unique().tolist()
    ccm_calcs_per_event = []
    for event_key in event_keys:
        event_data = all_match_data[all_match_data['event_key'] == event_key]
        season = int(event_key[:4])
        event_data = apply_season_specific_treatment(event_data, season)
        ccm_calcs = analyze_ccm(event_data)
        ccm_calcs['event_key'] = event_key
        ccm_calcs_per_event.append(ccm_calcs)

    return pd.concat(ccm_calcs_per_event)


def get_ccm_data_for_event(event_key):
    all_data = get_ccm_data()
    all_data = all_data[all_data['event_key'] == event_key]
    return all_data


def get_ccm_data_for_event_separated(event_key):
    all_data = get_ccm_data()
    all_data = all_data[all_data['event_key'] == event_key]
    return select_z_score_columns(all_data, ['team_id']), select_non_zscore_columns(all_data)


if __name__ == '__main__':
    m = cached_data.get_matches_for_event('2025week0')
    m = m[['key', 'red1', 'red2', 'red3', 'blue1', 'blue2', 'blue3', 'blue_score', 'red_score',
           'blue_auto_bonus_achieved', 'blue_rp', 'blue_coral_bonus_achieved', 'blue_barge_bonus_achieved',
           'red_auto_bonus_achieved', 'red_rp', 'red_coral_bonus_achieved', 'red_barge_bonus_achieved'
           ]]
    print(tabulate(m, headers='keys', tablefmt='psql', floatfmt=".3f"))
    print(tabulate(cached_data.get_oprs_and_ranks_for_event('2025week0'), headers='keys', tablefmt='psql',
                   floatfmt=".3f"))
