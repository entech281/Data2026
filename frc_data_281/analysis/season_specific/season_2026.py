"""2026 FRC Season-specific analysis.

The 2026 game features:
- Hub scoring: game pieces scored in a central hub across auto, teleop, and 4 shift zones
- Tower: robots climb a tower during auto and endgame periods
- RP achievements: Energized, Supercharged, Traversal
"""

import pandas as pd

from frc_data_281.analysis.dataset_tools import sum_matching_columns


def aggregate_hub_scoring(match_data_2026: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hub shift scoring into combined teleop hub totals.

    The match data has individual shift columns (shift1-shift4) plus teleop totals.
    This function is a no-op aggregation since TBA already provides total_count and
    total_points, but it's included here for consistency with the 2025 season structure
    and in case future aggregations are needed.

    Args:
        match_data_2026: DataFrame containing 2026 season match data.

    Returns:
        DataFrame (unchanged for now, hub totals already provided by TBA).
    """
    return match_data_2026


def _add_rp_columns(match_data: pd.DataFrame, rp_type: str, bonus_column: str) -> pd.DataFrame:
    """Add RP columns for a given bonus type.

    Args:
        match_data: Match data DataFrame.
        rp_type: Type of RP (e.g., 'win', 'energized', 'supercharged', 'traversal').
        bonus_column: Column name template with 'TEAM' as alliance placeholder.

    Returns:
        DataFrame with new RP columns added.
    """
    blue_rp_col = f'blue_{rp_type}_rp'
    red_rp_col = f'red_{rp_type}_rp'

    def calculate_rp(row):
        if row['comp_level'] != 'qm':
            return pd.Series({blue_rp_col: 0, red_rp_col: 0})

        if rp_type == 'win':
            if row['blue_score'] > row['red_score']:
                return pd.Series({blue_rp_col: 3, red_rp_col: 0})
            elif row['blue_score'] < row['red_score']:
                return pd.Series({blue_rp_col: 0, red_rp_col: 3})
            else:
                return pd.Series({blue_rp_col: 1, red_rp_col: 1})
        else:
            return pd.Series({
                blue_rp_col: (1 if row[bonus_column.replace('TEAM', 'blue')] == 1 else 0),
                red_rp_col: (1 if row[bonus_column.replace('TEAM', 'red')] == 1 else 0),
            })

    match_data[[blue_rp_col, red_rp_col]] = match_data.apply(calculate_rp, axis=1)
    return match_data


def add_scoring_computations(match_data_2026: pd.DataFrame) -> pd.DataFrame:
    """Add scoring computations for 2026 season.

    Adds RP calculations for win, Energized, Supercharged, and Traversal bonuses.

    Args:
        match_data_2026: DataFrame containing 2026 season match data.

    Returns:
        DataFrame with added RP columns.
    """
    match_data_2026 = _add_rp_columns(match_data_2026, 'win', "")
    match_data_2026 = _add_rp_columns(match_data_2026, 'energized', 'TEAM_energized_achieved')
    match_data_2026 = _add_rp_columns(match_data_2026, 'supercharged', 'TEAM_supercharged_achieved')
    match_data_2026 = _add_rp_columns(match_data_2026, 'traversal', 'TEAM_traversal_achieved')
    return match_data_2026
