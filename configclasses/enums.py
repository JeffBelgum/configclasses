"""
Common configuration enums provided for user convenience. However, any subclass of
python's ``enum.Enum`` will work as expected.
"""

import logging
from enum import Enum


class Environment(Enum):
    """
    Common environment names.
    """
    Development = 0
    Test = 1
    Staging = 2
    Production = 3


class LogLevel(Enum):
    """
    Python logging module log level constants represented as an ``enum.Enum``.
    """
    NotSet = logging.NOTSET
    Debug = logging.DEBUG
    Info = logging.INFO
    Warning = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL
