"""Entry point for running the FRC Data 281 Streamlit app.

Run with: python -m frc_data_281
"""
import sys
import subprocess
from pathlib import Path


def main():
    """Launch the Streamlit application."""
    app_path = Path(__file__).parent / "app" / "Home.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    cmd.extend(sys.argv[1:])
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
