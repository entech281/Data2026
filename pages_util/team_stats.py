from opr3 import *
import pandas as pd

def get_team_stats(team_number: int, df: pd.DataFrame) -> pd.DataFrame:
    """
    Get historical statistics for a specific team with both raw and z-scored metrics.
    
    Args:
        team_number (int): FRC team number
        df (pd.DataFrame): DataFrame containing data to analyze
        
    Returns:
        pd.DataFrame: DataFrame with raw metrics and z-scores over time
    """
    # Calculate raw OPR metrics
    raw_metrics = calculate_raw_opr(df)
    
    # Filter for specific team
    team_data = raw_metrics[raw_metrics['team_id'] == team_number]
    
    if len(team_data) == 0:
        return pd.DataFrame()
    
    # Add z-scores for numeric columns
    numeric_cols = team_data.select_dtypes(include=['float64', 'int64']).columns
    z_scores = add_zscores(team_data, numeric_cols)
    
    # Join raw and z-scored metrics
    result = pd.concat([team_data, z_scores], axis=1)
    
    # Clean and sort
    result = result.fillna(0)
    # result = result.sort_values(['event_key', 'match_number'])
    
    return result