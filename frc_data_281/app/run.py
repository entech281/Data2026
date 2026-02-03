"""Helper module to run the Streamlit app programmatically."""
import subprocess
import sys
from pathlib import Path


def run_app(args=None):
    """Run the Streamlit application.

    Args:
        args: Optional list of additional arguments to pass to Streamlit
    """
    app_path = Path(__file__).parent / "Home.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    if args:
        cmd.extend(args)
    return subprocess.call(cmd)


if __name__ == "__main__":
    run_app(sys.argv[1:])
