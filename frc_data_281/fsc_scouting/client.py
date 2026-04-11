"""Client for fetching scouting data from fscdata.org.

Supports two methods:
1. CSV export via POST to /report/export/generate_CSV (primary)
2. HTML table scraping from /report/raw/ (fallback)
"""

import io
import logging
import re

import pandas as pd
import requests

from frc_data_281.db.connection import get_connection

logger = logging.getLogger(__name__)

FSC_BASE_URL = "https://www.fscdata.org"
FSC_CSV_ENDPOINT = f"{FSC_BASE_URL}/report/export/generate_CSV"
FSC_RAW_ENDPOINT = f"{FSC_BASE_URL}/report/raw/"

# Maps TBA event keys to FSC event_id values
TBA_TO_FSC_EVENT = {
    "2026week0": 1,
    "2026sccha": 2,
    "2026schop": 3,
    "2026schar": 4,
    "2026sccmp": 5,
}

# Expected CSV columns from FSC export
FSC_CSV_COLUMNS = [
    "record_id", "match_number", "team_number",
    "auto_fuel_score", "auto_climb_try", "auto_climbed", "auto_traveled",
    "teleop_fuel_score", "teleop_traveled",
    "endgame_climb_try", "endgame_climb_level",
    "strategy_active_scored", "strategy_active_ferrying", "strategy_active_defense",
    "strategy_inactive_scored", "strategy_inactive_ferrying", "strategy_inactive_defense",
    "strategy_defense_actions",
    "match_fouls", "match_tipped", "match_broken", "match_beached", "match_carded",
    "match_disabled", "match_absent",
    "alliance_human_fuel",
]


def get_fsc_event_id(tba_event_key: str) -> int | None:
    """Map a TBA event key to an FSC event_id.

    Returns None if the event key has no FSC mapping.
    """
    return TBA_TO_FSC_EVENT.get(tba_event_key)


def fetch_scouting_csv(event_id: int, min_match: int = 0) -> pd.DataFrame:
    """Download scouting data as CSV from fscdata.org.

    Args:
        event_id: FSC numeric event identifier (1-5).
        min_match: Minimum match number to include (0 for all).

    Returns:
        DataFrame with scouting data, or empty DataFrame on failure.
    """
    try:
        response = requests.post(
            FSC_CSV_ENDPOINT,
            data={"event_id": event_id, "min_match_id": min_match},
            timeout=30,
        )
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))
        df = _normalize_dataframe(df)
        return df

    except requests.RequestException as e:
        logger.error("Failed to fetch CSV from fscdata.org: %s", e)
        return pd.DataFrame()
    except Exception as e:
        logger.error("Error parsing FSC CSV data: %s", e)
        return pd.DataFrame()


def scrape_scouting_html(event_id: int) -> pd.DataFrame:
    """Scrape scouting data from the HTML table at fscdata.org/report/raw/.

    Fallback method if CSV export is unavailable.

    Args:
        event_id: FSC numeric event identifier (1-5).

    Returns:
        DataFrame with scouting data, or empty DataFrame on failure.
    """
    try:
        response = requests.post(
            FSC_RAW_ENDPOINT,
            data={"event_id": event_id},
            timeout=30,
        )
        response.raise_for_status()

        headers, rows = _parse_html_table(response.text)
        if not rows:
            logger.warning("No data rows found in FSC HTML table for event_id=%d", event_id)
            return pd.DataFrame()

        # Use parsed headers if available, otherwise fall back to expected columns
        if headers and len(headers) == len(rows[0]):
            col_names = [
                re.sub(r"[^a-z0-9]+", "_", h.strip().lower()).strip("_")
                for h in headers
            ]
        else:
            # Trim rows to match the 24 visible HTML columns
            expected_cols = [
                "match_number", "team_number",
                "auto_fuel_score", "auto_climb_try", "auto_climbed", "auto_traveled",
                "teleop_fuel_score", "teleop_traveled",
                "endgame_climb_try", "endgame_climb_level",
                "strategy_active_scored", "strategy_active_ferrying", "strategy_active_defense",
                "strategy_inactive_scored", "strategy_inactive_ferrying", "strategy_inactive_defense",
                "strategy_defense_actions",
                "match_fouls", "match_carded", "match_tipped", "match_beached",
                "match_broken", "match_disabled", "match_absent",
            ]
            col_names = expected_cols
            rows = [r[:len(expected_cols)] for r in rows]

        df = pd.DataFrame(rows, columns=col_names)
        df = _normalize_dataframe(df)
        return df

    except requests.RequestException as e:
        logger.error("Failed to scrape HTML from fscdata.org: %s", e)
        return pd.DataFrame()
    except Exception as e:
        logger.error("Error parsing FSC HTML data: %s", e)
        return pd.DataFrame()


def _parse_html_table(html: str) -> tuple[list[str], list[list[str]]]:
    """Extract headers and data rows from an HTML table using regex.

    Returns:
        Tuple of (header_names, data_rows). Headers are extracted from visible
        <th> tags (ignoring commented-out ones). Data rows are trimmed to match
        the header count when possible.
    """
    headers = []
    rows = []

    # Extract visible headers (skip commented-out ones)
    thead_match = re.search(r"<thead>(.*?)</thead>", html, re.DOTALL)
    if not thead_match:
        return headers, rows

    th_pattern = re.compile(r"<th[^>]*>(.*?)</th>", re.DOTALL)
    headers = [th.strip() for th in th_pattern.findall(thead_match.group(1))]

    # Extract data rows from after </thead>
    tbody_html = html[thead_match.end():]
    tr_pattern = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)

    n_headers = len(headers)
    for tr_match in tr_pattern.finditer(tbody_html):
        cells = [cell.strip() for cell in td_pattern.findall(tr_match.group(1))]
        if cells:
            # Trim extra cells (from commented-out columns that still emit data)
            if n_headers > 0 and len(cells) > n_headers:
                cells = cells[:n_headers]
            rows.append(cells)

    return headers, rows


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and data types from FSC data."""
    # Normalize column names: lowercase, replace spaces/special chars with underscores
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", col.strip().lower()).strip("_")
        for col in df.columns
    ]

    # Strip whitespace from string values
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # Convert boolean-like columns
    bool_columns = [
        "auto_climb_try", "endgame_climb_try",
        "strategy_active_scored", "strategy_active_ferrying", "strategy_active_defense",
        "strategy_inactive_scored", "strategy_inactive_ferrying", "strategy_inactive_defense",
        "match_tipped", "match_broken", "match_beached", "match_carded",
        "match_disabled", "match_absent",
    ]
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].map(
                lambda x: True if str(x).strip().lower() == "true"
                else (False if str(x).strip().lower() == "false" else None)
            )

    # Convert numeric columns
    numeric_columns = [
        "record_id", "match_number", "team_number",
        "auto_fuel_score", "teleop_fuel_score",
        "strategy_defense_actions", "match_fouls", "alliance_human_fuel",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _upsert_scouting_data(event_key: str, df: pd.DataFrame):
    """Insert or replace scouting data into the database.

    Args:
        event_key: TBA event key to tag the data with.
        df: DataFrame of scouting data from FSC.
    """
    if df.empty:
        return

    df = df.copy()
    df["event_key"] = event_key

    with get_connection() as con:
        # Register the DataFrame as a temporary table and merge
        con.register("fsc_import", df)
        con.sql("""
            INSERT OR REPLACE INTO scouting.match_data (
                record_id, event_key, match_number, team_number,
                auto_fuel_score, auto_climb_try, auto_climbed, auto_traveled,
                teleop_fuel_score, teleop_traveled,
                endgame_climb_try, endgame_climb_level,
                strategy_active_scored, strategy_active_ferrying, strategy_active_defense,
                strategy_inactive_scored, strategy_inactive_ferrying, strategy_inactive_defense,
                strategy_defense_actions,
                match_fouls, match_tipped, match_broken, match_beached, match_carded,
                match_disabled, match_absent,
                alliance_human_fuel
            )
            SELECT
                record_id, event_key, match_number, team_number,
                auto_fuel_score, auto_climb_try, auto_climbed, auto_traveled,
                teleop_fuel_score, teleop_traveled,
                endgame_climb_try, endgame_climb_level,
                strategy_active_scored, strategy_active_ferrying, strategy_active_defense,
                strategy_inactive_scored, strategy_inactive_ferrying, strategy_inactive_defense,
                strategy_defense_actions,
                match_fouls, match_tipped, match_broken, match_beached, match_carded,
                match_disabled, match_absent,
                alliance_human_fuel
            FROM fsc_import
            WHERE match_number IS NOT NULL AND team_number IS NOT NULL
        """)
        con.unregister("fsc_import")


def sync_event(event_key: str):
    """Sync scouting data for a single event from fscdata.org.

    Args:
        event_key: TBA event key (e.g., '2026sccmp').
    """
    fsc_id = get_fsc_event_id(event_key)
    if fsc_id is None:
        logger.debug("No FSC mapping for event %s, skipping", event_key)
        return

    logger.info("Fetching FSC scouting data for %s (event_id=%d)...", event_key, fsc_id)
    df = fetch_scouting_csv(fsc_id)

    if df.empty:
        logger.info("No FSC scouting data available for %s, trying HTML fallback...", event_key)
        df = scrape_scouting_html(fsc_id)

    if df.empty:
        logger.warning("No FSC scouting data found for %s", event_key)
        return

    logger.info("Upserting %d scouting rows for %s", len(df), event_key)
    _upsert_scouting_data(event_key, df)


def sync_all_events(event_list: list[str]):
    """Sync scouting data for all events in the list.

    Args:
        event_list: List of TBA event keys.
    """
    for event_key in event_list:
        try:
            sync_event(event_key)
        except Exception as e:
            logger.error("Failed to sync FSC data for %s: %s", event_key, e)
