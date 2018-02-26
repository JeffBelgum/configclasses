"""
Common configuration enums provided for user convenience. However, any subclass of
`enum.Enum` will work as expected.
"""


from enum import Enum
import logging


class Environment(Enum):
    """
    Common environment names.
    """
    Production = 0
    Staging = 1
    Test = 2
    Development = 3


class LogLevel(Enum):
    """
    Python logging module log level constants represented as an `enum.Enum`.
    """
    NotSet = logging.NOTSET
    Debug = logging.DEBUG
    Info = logging.INFO
    Warn = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL
