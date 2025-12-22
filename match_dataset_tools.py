import pandas as pd
import json
import re
from scipy.stats import zscore
from dataclasses import dataclass
from typing import Union


def filter_for_team( df: pd.DataFrame, team_id:int)-> pd.DataFrame:
    return df[ df['team_id'] == team_id ]

def sum_matching_columns(df: pd.DataFrame, regex: str, new_column_name: str = "sum_matched",
                         remove_matched: bool = False) -> pd.DataFrame:
    """
    Adds a new column to the DataFrame that is the sum of columns matching the given regular expression.
    Optionally removes the matched columns after summing.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        regex (str): Regular expression pattern to match column names.
        new_column_name (str): Name of the new column to store the sum.
        remove_matched (bool): Whether to remove matched columns after summing.

    Returns:
        pd.DataFrame: A new DataFrame with the added column, optionally without the matched columns.
    """
    matched_columns = [col for col in df.columns if re.search(regex, col)]

    if not matched_columns:
        raise ValueError("No columns matched the given regex.")

    df[new_column_name] = df[matched_columns].sum(axis=1)

    if remove_matched:
        df = df.drop(columns=matched_columns)

    return df


def add_zscores ( df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    new_df = df.copy()
    cols = set(df.columns)
    cols.remove('team_id')
    cols_without_team = list(cols)
    for c in cols_without_team:
        new_df[c + "_z"] = zscore(df[c])
    return new_df


def drop_columns_with_word_in_column_name(df: pd.DataFrame , keyword:str) -> pd.DataFrame:

    cols_to_drop = []
    for c in df.columns:
        if c.find(keyword) >= 0:
            cols_to_drop.append(c)
    return df.drop(columns=cols_to_drop)

def find_columns_with_suffix(df: pd.DataFrame, suffix:str ):
    r = []
    for c in df.columns:
        if c.endswith(suffix):
            r.append(c)
    return r

def remove_from_list (original:list[str],to_remove:list[str] ) -> list[str]:
    return list( set(original) - set(to_remove))

"""
def column_map_for_color(columns:list,color:str) -> ( dict[str,str],list[str]):

    column_map = {
        color + "1":"t1",
        color + "2":"t2",
        color + "3":"t3",
    }

    if color == 'red':
        color_prefix,other_color_prefix = "red_","blue_"
    elif color == 'blue':
        color_prefix, other_color_prefix = "blue_", "red_"
    else:
        raise ValueError(f"Unknown color '{color}'")

    for c in columns:
        if c.startswith(color_prefix):
            column_map[c] = c.replace(color_prefix,"")
        elif c.startswith(other_color_prefix):
            column_map[c] = c.replace(other_color_prefix, "their_")
        else:
            # other columns are unmodified
            pass

    return column_map
"""


def unstack_data_from_color(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Unstacks match data to be one row per team, rather than one row per match.

    A typical match will have 6 team columns like red1, red2, red3, blue1,blue2,blue3,
    and fields named like red_? and blue_? for the values in the match.

    If the original dataframe has N rows ( 1 per match) , then this data can be transformed ( unstacked)
    into a new dataframe having 2*N rows, one per alliance per match,

    instead of red1, red2, red3 we have
    team1, team2, team3, and instead of red_<whatever> we have simply <whatever>, and
    other_<whatever> for the other allaiances score.

    This format is MUCH more convienient for OPR analysis.

    :param matches: a dataframe with 6 team columns like red1, red2, red3, blue1,blue2,blue3,
    and fields named like red_? and blue_? for the values in the match.
    :return:
    """

    red_column_map = column_map_for_color(matches,'red')
    blue_column_map = column_map_for_color(matches, 'blue')

    mapped_cols = set()
    mapped_cols.update(red_column_map.keys())
    mapped_cols.update(blue_column_map.keys())

    old_team_columns = ['red1','red2','red3','blue1','blue2','blue3']
    red_data = matches.rename(columns=red_column_map).drop(columns=['blue1','blue2','blue3'])
    blue_data = matches.rename(columns=blue_column_map).drop(columns=['red1','red2','red3'])
    all_data = pd.concat([red_data, blue_data])
    return all_data


def find_single_team_data( matches: pd.DataFrame) -> Union[None,pd.DataFrame]:
    """
    Finds columns that are provided for individual teams.
    Typically, this means there is a field like _robot1, _robot2, and _robot3
    Corresponding to teams red_one, etc
    If there are N fields encoded this way in match data:
       (1) 6 fields are used, one for each team
       (2) the result set will be 6x the rows of the original, but with only one field per
           group.
    Example:
        matches has 100 rows with columns:
           red1, red2, red3,
           blue1,blue2,blue3,
           red_park_robot1, red_park_robot2, red_park_robot3
           blue_park_robot1, blue_park_robot3, blue_park_robot3

        the result will have two columns:
        team, park
        with 600 rows.

    :param matches:
    :return: A dataframe having team number and values corresponding to detected
    fields, or NONE if the dataframe doesnt appear to have team-speicific data
    """
    all_columns = matches.columns
    team_fields = [ 'red1','red2','red3','blue1','blue2','blue3']
    if not (set(team_fields).issubset(set(all_columns))):
        print("Doesnt appear to have all team Fields in it!")
        return None

    found_columns = []
    finder = re.compile(r"^([r][e][d]|[b][l][u][e])_(.*)_robot(\d)", re.IGNORECASE)

    col_groups = {
        'red1': [],
        'red2': [],
        'red3': [],
        'blue1': [],
        'blue2': [],
        'blue3': []
    }

    for colname in all_columns:
        found = finder.match(colname)
        if found is not None:

            col_groups[found.group(1) + found.group(3)].append({
                'original_col': found.group(), # red_parked_robot1
                'new_col' : found.group(2) # parked
            })

    all_dfs = []

    for k,v in col_groups.items():
        cols_to_select = [k]
        rename_fields = { k: 'team'}

        for c in v:
            cols_to_select.append(c['original_col'])
            rename_fields[c['original_col']] = c['new_col']


        df_to_add = matches[cols_to_select].rename(columns=rename_fields)
        all_dfs.append(df_to_add)

    result = pd.concat(all_dfs,axis=0)
    return result
