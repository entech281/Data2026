import pandas as pd
from dataset_numerizer import numerize_dataset
from pandas.testing import assert_frame_equal


def test_basic_numerizer_defaults():
    """
    Maps that convert Booleans and strings to ints are automatically generated.
    Booleans:
        True: 1, False: 0
    Strings
        'Yes and No like' become 1 for Yes and 0 for NO
        otherwise, values are assigned ints beginning with 0, in order from most frequent to least frequent
    :return:
    """
    d = pd.DataFrame({
        'a': [ 1 , 0, 2],
        'b': [ True, False,False],
        'c' : [ 'foo', 'foo','bar']
    })
    r = numerize_dataset(d)
    assert {
        "b": {
            True: 1,
            False: 0
        },
        "c": {
            "foo": 0,
            "bar": 1
        }
    } == r.mapping

    MAPPED = pd.DataFrame({
        'a': [1, 0, 2],
        'b': [True, False, False],
        'c': ['foo', 'foo', 'bar'],
        'm_b': [1, 0, 0],
        'm_c': [0, 0, 1]
    })
    assert_frame_equal(d,r.original)
    assert_frame_equal( MAPPED,r.transformed)

def test_numerizer_overwrite_columns_with_empty_prefix():
    # with an empty prefix, the original columns are replaced
    d = pd.DataFrame({
        'a': [ 1 , 0, 2],
        'b': [ True, False,False],
        'c' : [ 'foo', 'foo','bar']
    })
    r = numerize_dataset(d,prefix="")
    assert {
        "b": {
            True: 1,
            False: 0
        },
        "c": {
            "foo": 0,
            "bar": 1
        }
    } == r.mapping

    MAPPED = pd.DataFrame({
        'a': [1, 0, 2],
        'b': [1, 0, 0],
        'c': [0, 0, 1]
    })
    assert_frame_equal(d,r.original)
    assert_frame_equal( MAPPED,r.transformed)


def test_basic_extra_mapping():
    d = pd.DataFrame({
        'a': [ 1 , 0, 2],
        'b': [ True, False,False],
        'c' : [ 'foo', 'foo','bar']
    })
    r = numerize_dataset(d,value_map_overrides={
        'c':{
            'foo': 2,
            'bar': 3
        }
    })
    assert {
        "b": {
            True: 1,
            False: 0
        },
        'c':{
            'foo': 2,
            'bar': 3
        }
    } == r.mapping

    MAPPED = pd.DataFrame({
        'a': [1, 0, 2],
        'b': [True, False, False],
        'c': ['foo', 'foo', 'bar'],
        'm_b': [1, 0, 0],
        'm_c': [2, 2, 3]
    })
    assert_frame_equal(d,r.original)
    assert_frame_equal( MAPPED,r.transformed)


def test_disabling_a_mapping():
    d = pd.DataFrame({
        'a': [ 1 , 0, 2],
        'b': [ True, False,False],
        'c' : [ 'foo', 'foo','bar']
    })
    r = numerize_dataset(d,value_map_overrides={
        'c':None
    })
    assert {
        "b": {
            True: 1,
            False: 0
        }
    } == r.mapping

    MAPPED = pd.DataFrame({
        'a': [1, 0, 2],
        'b': [True, False, False],
        'c': ['foo', 'foo', 'bar'],
        'm_b': [1, 0, 0]
    })
    assert_frame_equal(d,r.original)
    assert_frame_equal( MAPPED,r.transformed)


def test_numerizing_matches_using_skip_columns():
    matches = pd.read_parquet("./tests/data/matches.pq")
    r = numerize_dataset(matches, skip_columns=['key','event_key','comp_level','_dlt_id','_dlt_load_id'])
    assert len(matches) == len(r.transformed)

    assert {
        "blue_auto_line_robot1": {
            "Yes": 1,
            "No": 0
        },
        "blue_auto_line_robot2": {
            "Yes": 1,
            "No": 0
        },
        "blue_auto_line_robot3": {
            "Yes": 1,
            "No": 0
        },
        "blue_coop_note_played": {
            True: 1,
            False: 0
        },
        "blue_coopertition_bonus_achieved": {
            True: 1,
            False: 0
        },
        "blue_coopertition_criteria_met": {
            True: 1,
            False: 0
        },
        "blue_end_game_robot1": {
            "Parked": 0,
            "None": 1,
            "StageLeft": 2,
            "CenterStage": 3,
            "StageRight": 4
        },
        "blue_end_game_robot2": {
            "Parked": 0,
            "None": 1,
            "StageRight": 2,
            "StageLeft": 3,
            "CenterStage": 4
        },
        "blue_end_game_robot3": {
            "Parked": 0,
            "None": 1,
            "StageRight": 2,
            "CenterStage": 3,
            "StageLeft": 4
        },
        "blue_ensemble_bonus_achieved": {
            True: 1,
            False: 0
        },
        "blue_g206_penalty": {
            True: 1,
            False: 0
        },
        "blue_g408_penalty": {
            True: 1,
            False: 0
        },
        "blue_g424_penalty": {
            True: 1,
            False: 0
        },
        "blue_melody_bonus_achieved": {
            True: 1,
            False: 0
        },
        "blue_mic_center_stage": {
            True: 1,
            False: 0
        },
        "blue_mic_stage_left": {
            True: 1,
            False: 0
        },
        "blue_mic_stage_right": {
            True: 1,
            False: 0
        },
        "blue_trap_center_stage": {
            True: 1,
            False: 0
        },
        "blue_trap_stage_left": {
            True: 1,
            False: 0
        },
        "blue_trap_stage_right": {
            True: 1,
            False: 0
        },
        "red_auto_line_robot1": {
            "Yes": 1,
            "No": 0
        },
        "red_auto_line_robot2": {
            "Yes": 1,
            "No": 0
        },
        "red_auto_line_robot3": {
            "Yes": 1,
            "No": 0
        },
        "red_coop_note_played": {
            True: 1,
            False: 0
        },
        "red_coopertition_bonus_achieved": {
            True: 1,
            False: 0
        },
        "red_coopertition_criteria_met": {
            True: 1,
            False: 0
        },
        "red_end_game_robot1": {
            "Parked": 0,
            "None": 1,
            "StageLeft": 2,
            "CenterStage": 3,
            "StageRight": 4
        },
        "red_end_game_robot2": {
            "Parked": 0,
            "None": 1,
            "StageRight": 2,
            "StageLeft": 3,
            "CenterStage": 4
        },
        "red_end_game_robot3": {
            "Parked": 0,
            "None": 1,
            "StageRight": 2,
            "CenterStage": 3,
            "StageLeft": 4
        },
        "red_ensemble_bonus_achieved": {
            True: 1,
            False: 0
        },
        "red_g206_penalty": {
            True: 1,
            False: 0
        },
        "red_g408_penalty": {
            True: 1,
            False: 0
        },
        "red_g424_penalty": {
            True: 1,
            False: 0
        },
        "red_melody_bonus_achieved": {
            True: 1,
            False: 0
        },
        "red_mic_center_stage": {
            True: 1,
            False: 0
        },
        "red_mic_stage_left": {
            True: 1,
            False: 0
        },
        "red_mic_stage_right": {
            True: 1,
            False: 0
        },
        "red_trap_center_stage": {
            True: 1,
            False: 0
        },
        "red_trap_stage_left": {
            True: 1,
            False: 0
        },
        "red_trap_stage_right": {
            True: 1,
            False: 0
        }
    } == r.mapping



