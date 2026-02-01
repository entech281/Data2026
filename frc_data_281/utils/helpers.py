import json
import logging


def write_json_to_file(file_path: str, j):
    """Write JSON data to a file with indentation.

    Args:
        file_path: Path to output file.
        j: JSON-serializable data to write.
    """
    with open(file_path, 'w') as f:
        json.dump(j, f, indent=4)


def pretty_print_json(d: dict):
    """Pretty print a dictionary as formatted JSON.

    Args:
        d: Dictionary to print.
    """
    print(json.dumps(d, indent=4))


def setup_logging():
    """Configure basic logging with INFO level and formatted output."""
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                        handlers=[stream_handler])
