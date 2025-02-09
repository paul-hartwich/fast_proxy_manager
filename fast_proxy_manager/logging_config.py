import logging


def setup_logger():
    """Sets up the logger for the project."""
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)  # disables awful debug messages
