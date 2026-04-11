import dlt
from frc_data_281.the_blue_alliance import client as tba
from frc_data_281.utils import helpers as util
from frc_data_281.db import connection
from frc_data_281.db.schema import create_schema
import logging

logger = logging.getLogger(__name__)
loop_delay_secs = 5


def set_loop_delay(new_delay_secs):
    """Set the delay between pipeline loops.

    Args:
        new_delay_secs: Delay in seconds.
    """
    global loop_delay_secs
    loop_delay_secs = new_delay_secs


def everyone_use_the_same_logger():
    """Get the module logger for shared use.

    Returns:
        Logger instance.
    """
    return logger


@dlt.resource(table_name="teams", write_disposition='merge', primary_key='key')
def sync_teams_source(event_list):
    """DLT resource to sync team data for events.

    Args:
        event_list: List of event keys to sync.

    Yields:
        Team data from TBA API.
    """
    for event_name in event_list:
        yield from tba.get_teams_for_event(event_name)


@dlt.resource(table_name='matches', write_disposition='merge', primary_key='key')
def sync_matches_source(event_list):
    """DLT resource to sync match data for events.

    Args:
        event_list: List of event keys to sync.

    Yields:
        Match data from TBA API.
    """
    for event_name in event_list:
        yield from tba.get_matches_for_event(event_name)


@dlt.resource(table_name='oprs', write_disposition='merge', primary_key=['team_number', 'event_key'])
def event_opr_source(event_list):
    """DLT resource to sync OPR data for events.

    Args:
        event_list: List of event keys to sync.

    Yields:
        OPR data from TBA API.
    """
    for event_name in event_list:
        yield from tba.get_event_oprs(event_name)


@dlt.resource(table_name='event_rankings', write_disposition='merge', primary_key=['team_number', 'event_key'])
def event_rankings_source(event_list):
    """DLT resource to sync event rankings for events.

    Args:
        event_list: List of event keys to sync.

    Yields:
        Event rankings data from TBA API.
    """
    for event_name in event_list:
        yield from tba.get_event_rankings(event_name)


@dlt.resource(table_name='rankings', write_disposition='merge', primary_key=['team_number', 'event_key'])
def district_rankings_source():
    """DLT resource to sync district rankings.

    Yields:
        District rankings data from TBA API.
    """
    yield from tba.get_rankings_for_district()


def sync():
    """Execute the full TBA data sync pipeline."""
    create_schema()

    print("DLT Vars:", dlt.config)
    pipeline = dlt.pipeline(
        pipeline_name='2026sc',
        destination=dlt.destinations.duckdb(connection.DB_PATH),
        dataset_name='tba'
    )

    event_list = ['2026sccmp', '2026sccha', '2026schop', '2026schar']

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

    # Sync FSC scouting data (match-level observations from human scouts)
    logger.info("Sync FSC Scouting Data...")
    from frc_data_281.fsc_scouting.client import sync_all_events
    sync_all_events(event_list)

    logger.warning("Sync Complete!")


if __name__ == '__main__':
    util.setup_logging()
    sync()
