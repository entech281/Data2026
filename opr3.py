import pandas as pd
import sys
from motherduck import con
import cached_data
import numpy as np
from scipy.stats import zscore
import cachetools.func
import time
from match_dataset_tools import unstack_data_from_color,drop_columns_with_word_in_column_name,add_zscores,find_columns_with_suffix,sum_matching_columns,remove_from_list
from tabulate import tabulate
CCM_CACHE_SECONDS=60


def column_map_for_color(columns:list,color:str) -> ( dict[str,str],list[str]):
    column_map = {
        color + "1":"t1",
        color + "2":"t2",
        color + "3":"t3",
    }
    automapped_fields = set()
    if ( color == "red"):
        column_map["blue_score"] = "their_score"

    if ( color == "blue"):
        column_map["red_score"] = "their_score"

    color_prefix = color + "_"
    #get columns associated with this team, like team_<value>
    for c in columns:
        if c.startswith(color_prefix):
            computed_field = c.replace(color_prefix,"")
            automapped_fields.add(computed_field)
            column_map[c] = computed_field

    #print("Col map=",column_map)
    return column_map,list(automapped_fields)


def _calculate_opr_ccwm_dpr(matches: pd.DataFrame) -> pd.DataFrame:
    #get the unique list of teams
    team_list = pd.unique(matches[['red1','red2','red3','blue1','blue2','blue3']].values.ravel('K'))
    #print("Unique Teams: One column, num rows= Nteams ")
    #score_cols = extract_red_and_blue_columns(matches)

    #lets only consider numeric columns for now. later we can add converters for booleans and strings
    numeric_columns = matches.select_dtypes(include='number').columns
    red_col_map,automapped_fields = column_map_for_color(numeric_columns,'red')
    blue_col_map,automapped_fields = column_map_for_color(numeric_columns,'blue')

    red_data = matches.rename(columns=red_col_map)
    blue_data = matches.rename(columns=blue_col_map)

    all_data = pd.concat([red_data,blue_data])
    all_data['margin'] = all_data['score'] - all_data['their_score']


    m=[]
    for idx,match in all_data.iterrows():
        r=[]
        for team in team_list:
            if match['t1'] == team or match['t2'] == team or match['t3'] == team:
                r.append(1)
            else:
                r.append(0)
        m.append(r)
    m_m = np.matrix(m)

    #left side values are all the columsn in the map, MINUS a key few
    computed_cols = ['margin','their_score'] + automapped_fields

    #left_side = all_data[['our_score','their_score','margin']]
    left_side = all_data[computed_cols]
    #print("left Side")
    #print(left_side)
    c_c = np.matrix(left_side)

    pseudo_inverse = np.linalg.pinv(m_m)
    computed = np.matmul(pseudo_inverse,c_c)

    results_2 = pd.DataFrame(computed,columns=computed_cols)
    teams_2 = pd.DataFrame(team_list,columns=['team_id'])
    results_all = pd.concat([teams_2, results_2], axis=1)

    return results_all.sort_values(by=['score'],ascending=False)


def add_zscores(df:pd.DataFrame, cols:list[str]) -> pd.DataFrame:

    new_df = df.copy()
    for c in cols:
        new_df[c + "_z"] = zscore(df[c])
    return new_df


def analyze_ccm(df: pd.DataFrame) -> pd.DataFrame:
    matches = df
    r = _calculate_opr_ccwm_dpr(matches)
    r = drop_columns_with_word_in_column_name(r,'threshold') #robot1,2, 3 are robot specific, we can get those later
    r = drop_columns_with_word_in_column_name(r, '_robot')
    cols_to_use = remove_from_list(r.columns, [ 'team_id'])
    with_z = add_zscores(r, cols_to_use)
    return with_z


def add_scoring_computations(match_data_2025: pd.DataFrame) -> pd.DataFrame:
    #it would reduce the code here to do this inside of calculate_opr_ccwm_dpr, but i dont
    #want that function to have season specific stuff, so we adjust here even though its a bit more work

    match_data_2025['blue_total_coral_points'] = match_data_2025['blue_teleop_coral_points'] + match_data_2025['blue_auto_coral_points']
    match_data_2025['red_total_coral_points'] = match_data_2025['red_teleop_coral_points'] + match_data_2025['red_auto_coral_points']
    match_data_2025['blue_total_coral_count'] = match_data_2025['blue_teleop_coral_count'] + match_data_2025['blue_auto_coral_count']
    match_data_2025['red_total_coral_count'] = match_data_2025['red_teleop_coral_count'] + match_data_2025['red_auto_coral_count']

    #rp calculations
    #annoyting: this is different than the code here:
    #def get_ranking_point_summary_for_event(event_key:str) -> pd.DataFrame:
    #but that version is not vectorized

    # 3 rp for win
    # 1 rp for tie
    def win_rp(row):
        if row['comp_level'] != 'qm':
            return pd.Series({
                'blue_win_rp': 0,
                'red_win_rp': 0
            })
        if row['blue_score'] > row['red_score']:
            return pd.Series({
                'blue_win_rp': 3,
                'red_win_rp': 0
            })
        elif row['blue_score'] < row['red_score']:
            return pd.Series({
                'blue_win_rp': 0,
                'red_win_rp': 3
            })
        else: #equal
            return pd.Series({
                'blue_win_rp': 1,
                'red_win_rp': 1
            })
    match_data_2025[['blue_win_rp','red_win_rp']] = match_data_2025.apply(win_rp,axis=1)

    # 1 rp for auto: all three must move and at least one coral in auto
    def auto_rp(row):
        if row['comp_level'] != 'qm':
            return pd.Series({
                'blue_auto_rp': 0,
                'red_auto_rp': 0
            })

        return pd.Series({
            'blue_auto_rp': (1 if row['blue_auto_bonus_achieved'] == 1  else 0),
            'red_auto_rp': (1 if row['red_auto_bonus_achieved'] == 1  else 0),
        })
    match_data_2025[['blue_auto_rp', 'red_auto_rp']] = match_data_2025.apply(auto_rp, axis=1)

    def coral_rp(row):
        if row['comp_level'] != 'qm':
            return pd.Series({
                'blue_coral_rp': 0,
                'red_coral_rp': 0
            })

        return pd.Series({
            'blue_coral_rp': (1 if row['blue_coral_bonus_achieved'] == 1  else 0),
            'red_coral_rp': (1 if row['red_coral_bonus_achieved'] == 1  else 0),
        })
    match_data_2025[['blue_coral_rp', 'red_coral_rp']] = match_data_2025.apply(coral_rp, axis=1)

    def barge_rp(row):
        if row['comp_level'] != 'qm':
            return pd.Series({
                'blue_barge_rp': 0,
                'red_barge_rp': 0
            })

        return pd.Series({
            'blue_barge_rp': (1 if row['blue_barge_bonus_achieved'] == 1  else 0),
            'red_barge_rp': (1 if row['red_barge_bonus_achieved'] == 1  else 0),
        })
    match_data_2025[['blue_barge_rp', 'red_barge_rp']] = match_data_2025.apply(barge_rp, axis=1)

    return match_data_2025


def aggregate_reef_scoring(match_data_2025: pd.DataFrame) -> pd.DataFrame:

    #TODO: clearly a more clever way that could also work in later seasons would be nice
    match_data_2025 = sum_matching_columns(match_data_2025,r'^blue_auto_reef_bot_row_node','blue_auto_reef_bot_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^blue_auto_reef_mid_row_node', 'blue_auto_reef_mid_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^blue_auto_reef_top_row_node', 'blue_auto_reef_top_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025,r'^red_auto_reef_bot_row_node','red_auto_reef_bot_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^red_auto_reef_mid_row_node', 'red_auto_reef_mid_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^red_auto_reef_top_row_node', 'red_auto_reef_top_row',True)

    match_data_2025 = sum_matching_columns(match_data_2025,r'^blue_teleop_reef_bot_row_node','blue_teleop_reef_bot_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^blue_teleop_reef_mid_row_node', 'blue_teleop_reef_mid_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^blue_teleop_reef_top_row_node', 'blue_teleop_reef_top_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025,r'^red_teleop_reef_bot_row_node','red_teleop_reef_bot_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^red_teleop_reef_mid_row_node', 'red_teleop_reef_mid_row',True)
    match_data_2025 = sum_matching_columns(match_data_2025, r'^red_teleop_reef_top_row_node', 'red_teleop_reef_top_row',True)

    return match_data_2025


def select_z_score_columns( df:pd.DataFrame, other_columns=[]):
    weighted_columns = find_columns_with_suffix(df, "_z") +other_columns
    return df[weighted_columns]

def select_non_zscore_columns(df: pd.DataFrame ):
    zscore_columns = find_columns_with_suffix(df, "_z")
    return df.drop(columns=zscore_columns)

@cachetools.func.ttl_cache(maxsize=128, ttl=CCM_CACHE_SECONDS)
def get_ccm_data() -> pd.DataFrame:
    print("This is the new version of get_ccm_data")
    all_match_data = cached_data.get_matches()
    print(f"Before Filter {len(all_match_data)}")
    all_match_data = all_match_data[ all_match_data["winning_alliance"].notna() ]
    all_match_data = all_match_data[all_match_data["winning_alliance"] != '']
    print(f"After Filter {len(all_match_data)}")
    event_keys = all_match_data['event_key'].unique().tolist()

    r = []
    for event_key in event_keys:
        filtered_for_event = all_match_data[ all_match_data['event_key'] == event_key]
        filtered_for_event = aggregate_reef_scoring(filtered_for_event)
        with_other_computations = add_scoring_computations(filtered_for_event)
        ccm_calcs = analyze_ccm(with_other_computations)
        ccm_calcs['event_key'] = event_key
        r.append(ccm_calcs)

    return pd.concat(r)


def get_ccm_data_for_event(event_key):
    all_data = get_ccm_data()
    all_data = all_data[all_data['event_key'] == event_key]
    return all_data


def get_ccm_data_for_event_separated(event_key):
    all_data = get_ccm_data()
    all_data = all_data[all_data['event_key'] == event_key]
    return select_z_score_columns(all_data, ['team_id']),select_non_zscore_columns(all_data)


if __name__  == '__main__':
    m = cached_data.get_matches_for_event('2025week0')
    m = m[ ['key','red1', 'red2', 'red3', 'blue1','blue2','blue3','blue_score','red_score',
            'blue_auto_bonus_achieved','blue_rp','blue_coral_bonus_achieved','blue_barge_bonus_achieved',
            'red_auto_bonus_achieved', 'red_rp','red_coral_bonus_achieved', 'red_barge_bonus_achieved'
    ]]
    print(tabulate(m, headers='keys', tablefmt='psql', floatfmt=".3f"))
    print(tabulate(cached_data.get_oprs_and_ranks_for_event('2025week0'), headers='keys', tablefmt='psql', floatfmt=".3f"))



