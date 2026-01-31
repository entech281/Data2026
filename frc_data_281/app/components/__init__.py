"""Reusable Streamlit components for the FRC Data 281 app."""

from pathlib import Path


def get_static_path(filename: str) -> str:
    """Get the absolute path to a static file bundled with the package.

    Args:
        filename: The name of the static file (e.g., '281.png')

    Returns:
        The absolute path to the static file as a string
    """
    return str(Path(__file__).parent.parent / "static" / filename)


def get_config_path(filename: str) -> str:
    """Get the absolute path to a config file bundled with the package.

    Args:
        filename: The name of the config file (e.g., 'gw_config.json')

    Returns:
        The absolute path to the config file as a string
    """
    return str(Path(__file__).parent.parent / "config" / filename)
