import logging
import sys


LOG = logging.getLogger()


def _init_logger() -> None:
    """
    Set up the logger for the project.

    Should only be called once upon import.
    """

    LOG.setLevel(logging.DEBUG)

    # Create a formatter
    log_formatter = logging.Formatter(
        "%(asctime)s :: %(funcName)s<@>%(threadName)s [%(levelname)-1.1s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if "--verbose" in sys.argv else logging.INFO)
    console_handler.setFormatter(log_formatter)

    # Add the handlers to the logger
    LOG.addHandler(console_handler)


_init_logger()
