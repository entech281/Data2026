"""
FRC Data 281 - Scouting data analysis for FRC Team 281

This package provides tools for FRC competition scouting and data analysis,
including integration with The Blue Alliance API and a Streamlit-based UI.
"""

__version__ = "0.2.0"

from frc_data_281.db import get_connection
from frc_data_281.db import cached_queries
from frc_data_281.analysis import opr
