"""Logging setup.

PRIVACY RULE: never log extracted document text, lab values, medication names,
or file contents. Log only IDs, status codes, timings and error codes.
"""
import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
