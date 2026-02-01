import pandas as pd

from frc_data_281.analysis.dataset_tools import sum_matching_columns


def aggregate_reef_scoring(match_data_2025: pd.DataFrame) -> pd.DataFrame:
    """Aggregate reef scoring metrics.

    The match data has a column for each scoring position on the reef. There are nodes
    (around the reef perimeter) and rows (top, middle, bottom). This function sums the
    node columns, leaving a single column for all nodes at a given row. For example,
    columns "blue_auto_reef_bot_row_node_a", "blue_auto_reef_bot_row_node_b", etc. are
    summed into a single column for the bottom row.

    Args:
        match_data_2025: DataFrame containing 2025 season match data with reef scoring columns.

    Returns:
        DataFrame with aggregated reef scoring columns.
    """

    # assemble all metric names, for example "auto_reef_mid_row"
    reef_metrics = []
    for mode in ["auto", "teleop"]:
        for height in ["top", "mid", "bot"]:
            reef_metrics.append(f"{mode}_reef_{height}_row")

    # for each team, sum the various metric columns
    for team_color in ["blue", "red"]:
        for reef_metric in reef_metrics:
            match_data_2025 = sum_matching_columns(
                match_data_2025,
                regex=rf'^{team_color}_{reef_metric}_node',
                new_column_name=f'{team_color}_{reef_metric}',
                remove_matched=True,
            )

    return match_data_2025


def _add_coral_totals(match_data: pd.DataFrame) -> pd.DataFrame:
    """Add total coral points and counts by summing auto and teleop values.

    Args:
        match_data: DataFrame containing match data with separate auto and teleop coral metrics.

    Returns:
        DataFrame with added total coral points and count columns.
    """
    for team_color in ['blue', 'red']:
        for metric_type in ['points', 'count']:
            match_data[f'{team_color}_total_coral_{metric_type}'] = (
                match_data[f'{team_color}_teleop_coral_{metric_type}'] +
                match_data[f'{team_color}_auto_coral_{metric_type}']
            )
    return match_data


def _add_rp_columns(match_data: pd.DataFrame, rp_type: str, bonus_column: str) -> pd.DataFrame:
    """Add RP columns for a given bonus type.

    Args:
        match_data: Match data DataFrame
        rp_type: Type of RP (e.g., 'win', 'auto', 'coral', 'barge')
        bonus_column: Column name containing the bonus achievement flag

    Returns:
        DataFrame with new RP columns added
    """
    blue_rp_col = f'blue_{rp_type}_rp'
    red_rp_col = f'red_{rp_type}_rp'

    def calculate_rp(row):
        # Non-qualification matches get 0 RP
        if row['comp_level'] != 'qm':
            return pd.Series({blue_rp_col: 0, red_rp_col: 0})

        if rp_type == 'win':
            # Win RP: 3 for win, 1 for tie, 0 for loss
            if row['blue_score'] > row['red_score']:
                return pd.Series({blue_rp_col: 3, red_rp_col: 0})
            elif row['blue_score'] < row['red_score']:
                return pd.Series({blue_rp_col: 0, red_rp_col: 3})
            else:  # tie
                return pd.Series({blue_rp_col: 1, red_rp_col: 1})
        else:
            # Other RP types: 1 if bonus achieved, 0 otherwise
            return pd.Series({
                blue_rp_col: (1 if row[bonus_column.replace('TEAM', 'blue')] == 1 else 0),
                red_rp_col: (1 if row[bonus_column.replace('TEAM', 'red')] == 1 else 0),
            })

    match_data[[blue_rp_col, red_rp_col]] = match_data.apply(calculate_rp, axis=1)
    return match_data


def add_scoring_computations(match_data_2025: pd.DataFrame) -> pd.DataFrame:
    """Add scoring computations for 2025 season.

    Adds total coral metrics and RP (Ranking Points) calculations for various bonuses.

    Args:
        match_data_2025: DataFrame containing 2025 season match data.

    Returns:
        DataFrame with added scoring computations and RP columns.
    """
    # Add coral totals
    match_data_2025 = _add_coral_totals(match_data_2025)

    # Add RP calculations
    match_data_2025 = _add_rp_columns(match_data_2025, 'win', "")
    match_data_2025 = _add_rp_columns(match_data_2025, 'auto', 'TEAM_auto_bonus_achieved')
    match_data_2025 = _add_rp_columns(match_data_2025, 'coral', 'TEAM_coral_bonus_achieved')
    match_data_2025 = _add_rp_columns(match_data_2025, 'barge', 'TEAM_barge_bonus_achieved')

    return match_data_2025

