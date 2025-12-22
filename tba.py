import requests
import json
import logging
import pandas as pd
from io import StringIO
from datetime import datetime,date
import time
import streamlit as st
from flatten_json import flatten
logger = logging.getLogger(__name__)


def set_logger(new_logger):
    global logger
    logger = new_logger

DATE_FORMAT="%Y-%m-%d"
TBA_ACCESS_TOKEN=st.secrets['tba']['auth_key']
TBA_API_ROOT = 'https://www.thebluealliance.com/api/v3/'
DISTRICT_KEY='2025fsc'
DISTRICT_EVENTS=[ '2025schar','2025sccha', '2025sccmp' ]

def change_dict_yesnos_to_booleans(d: dict) -> dict:
    def change_yesno_boolean_to_zero_one(value):
        if value in ["Yes", "Y", "Yup", "yes", "y", True,"true","True"]:
            return 1
        if value in ["N", "n", "No", 'no', False,"false","False"]:
            return 0
        return value

    r = {}

    for k,v in d.items():
        r[k] = change_yesno_boolean_to_zero_one(v)
    return r


def team_number_from_key(frc_team_key):
    return int(frc_team_key.replace('frc', ''))


def get_fields(from_dict:dict, fields:list[str])-> dict:
    r = {}
    for f in fields:
        if f in from_dict.keys():
            r[f] = from_dict[f]
    return r


def _get(url, result_type='json'):

    response = requests.get(TBA_API_ROOT + url, headers={
        'X-TBA-Auth-Key': TBA_ACCESS_TOKEN
    })
    if result_type == 'json':
        return response.json()
    else:
        return response.text


def get_teams_for_district():
    return _get(f'/district/{DISTRICT_KEY}/teams')


def get_teams_for_event(event_name):
    return _get(f'/event/{event_name}/teams')


def get_matches_for_event(event_name):
    matches= _get("/event/{event_key}/matches".format(event_key=event_name))

    def flatten_match(match):
        r = get_fields(match, ['time','predicted_time','set_number','winning_alliance', 'actual_time','match_number','key','event_key','comp_level'])
        blue_teams = match["alliances"]["blue"]["team_keys"]
        red_teams = match["alliances"]["red"]["team_keys"]
        r["red1"] = team_number_from_key(red_teams[0])
        r["red2"] = team_number_from_key(red_teams[1])
        r["red3"] = team_number_from_key(red_teams[2])
        r['red_score'] =  match['alliances']['red']['score']
        r["blue1"] = team_number_from_key(blue_teams[0])
        r["blue2"] = team_number_from_key(blue_teams[1])
        r["blue3"] = team_number_from_key(blue_teams[2])
        r['blue_score'] = match['alliances']['blue']['score']

        if match['score_breakdown']:
            score_breakdown = flatten(match['score_breakdown'])
            score_breakdown = change_dict_yesnos_to_booleans(score_breakdown)
            r.update(flatten(score_breakdown))

        return r

    retval = [flatten_match(m) for m in matches]
    return retval


def zero_if_column_missing(df,col_name):
    df_return = df
    if col_name not in df.columns:
        df_return[col_name] = 0
    return df_return


def get_event_rankings(event_key):
    r = _get("/event/{event_key}/rankings".format(event_key=event_key))
    if r is None:
        return []

    def flatten_record(rec):
        r = get_fields(rec,['dq','matches_played','qual_average','rank','team_key'])
        r['team_number'] = team_number_from_key(rec['team_key'])
        r['event_key'] = event_key
        if 'record' in rec:
            r['wins'] = rec['record']['wins']
            r['losses'] = rec['record']['losses']
            r['ties'] = rec['record']['ties']
        return r

    return [ flatten_record(x) for x in r['rankings']]


def get_event_oprs(event_key):

    r = _get("/event/{event_key}/oprs".format(event_key=event_key), result_type='text')
    df = pd.read_json(StringIO(r), orient='columns').reset_index()
    df['team_number'] = df['index'].apply(team_number_from_key)

    df = zero_if_column_missing(df,'oprs')
    df = zero_if_column_missing(df, 'dprs')
    df = zero_if_column_missing(df, 'ccwms')
    df = zero_if_column_missing(df, 'team_number')

    df = df[['team_number', 'oprs', 'dprs', 'ccwms']]
    df['event_key'] = event_key
    return df.to_dict('records')


def get_rankings_for_district():
    rankings = _get(f'/district/{DISTRICT_KEY}/rankings')
    if rankings is not None:
        return rankings.json()
    else:
        return []


def setup_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                        handlers=[stream_handler])


if __name__ == '__main__':
    setup_logging()
    #print ( json.dumps(get_rankings_for_district(),indent=4))''
    #print(json.dumps(get_event_rankings('2025schar'), indent=4))
    r=get_event_rankings('2025schar')
    print(r)