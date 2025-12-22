import dlt
import tba
import util
import logging
import os
import streamlit as st
from datetime import datetime
import motherduck
logger = logging.getLogger(__name__)
loop_delay_secs=5

def set_loop_delay(new_delay_secs):
    global loop_delay_secs
    loop_delay_secs = new_delay_secs

def everyone_use_the_same_logger():
    return logger


@dlt.resource(table_name="teams", write_disposition='merge', primary_key='key')
def sync_teams_source(event_list):
    for event_name in event_list:
        yield from  tba.get_teams_for_event(event_name)


@dlt.resource(table_name='matches', write_disposition='merge', primary_key='key')
def sync_matches_source(event_list):
    for event_name in event_list:
        yield from tba.get_matches_for_event(event_name)


@dlt.resource(table_name='oprs', write_disposition='merge', primary_key=['team_number','event_key'])
def event_opr_source(event_list):
    for event_name in event_list:
        yield from tba.get_event_oprs(event_name)


@dlt.resource(table_name='event_rankings', write_disposition='merge', primary_key=['team_number','event_key'])
def event_rankings_source(event_list):
    for event_name in event_list:
        yield from tba.get_event_rankings(event_name)


@dlt.resource(table_name='rankings', write_disposition='merge', primary_key=['team_number','event_key'])
def district_rankings_source():
    yield from tba.get_rankings_for_district()


def sync():

    print("DLT Vars:",dlt.config)
    pipeline = dlt.pipeline(
        pipeline_name='2025sc',
        destination=dlt.destinations.duckdb(motherduck.con),
        dataset_name='tba'
    )

    event_list =  ['2025week0','2025mnkk','2025mndu2','2025sccha','2025gagai','2025sccmp','2025schar']

    logger.info("Sync Teams...")
    load_info = pipeline.run(sync_teams_source(event_list))
    logger.info(load_info)

    logger.info("Sync Matches...")
    load_info = pipeline.run(sync_matches_source(event_list))
    logger.info(load_info)

    logger.info("Sync Rankings...")
    load_info = pipeline.run(event_rankings_source(event_list))
    logger.info(load_info)

    logger.info("Sync Oprs...")
    load_info = pipeline.run(event_opr_source(event_list))
    logger.info(load_info)

    logger.warning("Sync Complete!")


if __name__ == '__main__':
    util.setup_logging()
    sync()

