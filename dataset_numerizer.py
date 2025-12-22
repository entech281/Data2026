import pandas as pd
import json
from dataclasses import dataclass
from typing import Union
"""
Accepts a dataframe with non-numeric values and attempst to convert them to numbers 

"""

@dataclass
class MappedDataFrame:
    original: pd.DataFrame
    prefix: str
    mapping: dict[str,dict]
    transformed: pd.DataFrame


def convert_bool(b):
    if b:
        return 1
    else:
        return 0


def xref_column_with_map(col,value_map:dict[str,object]) -> pd.Series:
    return col.map(value_map)


def get_map_if_looks_like_boolean_in_form_of_string(col) -> Union[dict,None]:
    if pd.api.types.is_string_dtype(col.dtype):
        col_vals = set(col.unique())
        if col_vals == {"Yes", "No"}:
            return {"Yes": 1, "No": 0}

        if col_vals == {"Y", "N"}:
            return {"Y": 1, "N": 0}

        if col_vals == {"yes", "no"}:
            return {"yes": 1, "no": 0}
    return None


def get_map_of_ints_based_on_values(col) -> dict[object,int]:
    value_counts = col.value_counts()
    value_map = {}
    index = 0
    for i, v in value_counts.items():
        value_map[i] = index
        index += 1
    return value_map


def get_automap_for_column(col:pd.Series) -> Union[None,dict[object,int]]:

    if col.dtype == 'bool':
        return {
            True: 1,
            False: 0
        }
    if pd.api.types.is_string_dtype(col.dtype):
        m = get_map_if_looks_like_boolean_in_form_of_string(col)
        if m is not None:
            return m
        else:
            return get_map_of_ints_based_on_values(col)

    return None


def xref_column_with_automap(col:pd.Series) -> pd.Series :
    value_map = get_automap_for_column(col)

    if value_map is not None:

        def mapvalue(v):
            return value_map.get(v, None)

        return col.map(mapvalue)
    else:
        return col


def generate_dataset_maps( df: pd.DataFrame)-> dict[str,dict[object,int]]:
    "Automatically generate a guess for dataset maps to convert things to numeric types"
    result_map = {}

    for cname in df.columns:
        col = df[cname]
        m = get_automap_for_column(col)
        if m != None:
            result_map[col.name] = m

    return result_map


def numerize_dataset(original:pd.DataFrame, prefix:str ='m_', value_map_overrides={},skip_columns:list[str] =[]) -> MappedDataFrame:
    """
    Provide Numeric Values in place of booleans and string columns, whenever possible
    :param original: The original, unmodified data frame
    :param prefix: The prefix to use for transformed columns. empty("") means overwrite the original column
    :param value_map_overrides:  a dict with key=column name, and value dict that cross-references values to ints. A mapping with value
    None will disable mappings for the associated column
    :param skip_columns a list of columns to skip. If provided, this is equivalent to providing an empty dict with a None mapping in value_map_overrides
    :return: MappedDataFrame,which contains the mappings used, the orignal, and transformed dataframes
    the mapping returned is the effective mapping-- only containing keys that actually changed values in a column
    """
    result = original.copy()

    # Note that user provided values override detault provided ones!
    mapping = {}
    mapping.update(generate_dataset_maps(original))
    mapping.update(value_map_overrides)

    for skip_col_name in skip_columns:
        mapping[skip_col_name] = None

    # remove mappings with None-- this cleans up output
    effective_mapping = {}
    for k,v in mapping.items():
        if v is not None:
            effective_mapping[k] = v

    for colname in result.columns:
        m = effective_mapping.get(colname,None)
        if m is not None:
            result[prefix + colname ] = xref_column_with_map(result[colname],m)

    return MappedDataFrame(original=original, prefix=prefix, mapping=effective_mapping, transformed=result)



