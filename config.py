import os
from enum import Enum
from functools import wraps
from types import FunctionType
import json
import logging
import sys

from dataclasses import dataclass, MISSING
import requests

_CONFIGURATION_SINGLETON = None
_CONFIGURATION_SINGLETON_INIT = False

# TODO: reload method (Threadsafe?)
#
# TOO Magical:
#   case insensitivity/canonicalization
#   env_var namespacing??
#   enum get by value? (I think this is ok)
#
#
# Needs:
#   async/sync
#   reload (threadsafe)
#   reader or source better name?
#   cli reader
#   deal with values that are parsed as strings always and values that aren't
#     e.g. environment variables vs json data
#
#   field(converter=lambda)
#     ?section?
#
#   ? Hooks to support push style reloads instead of only polling ?
#
#   more tests
#   nice generated docs

class Reader:
    """
    Reader knows how to get values out of a `canonical_kv_mapping` instance field
    or return a default
    """
    def get(self, field, default=MISSING):
        value = self.canonical_kv_mapping.get(field.upper(), MISSING)
        if value is MISSING:
            return default
        return value


class EnvironmentReader(Reader):
    """
    Get configuration values from case insensitive environment variables.
    """
    def __init__(self, namespace=None, environ=os.environ):
        self.namespace = namespace
        self.canonical_kv_mapping = {}
        for key, value in environ.items():
            if self.namespace is not None:
                key = key[len(self.namespace):]
            self.canonical_kv_mapping[key.upper()] = value

class CommandLineReader(Reader):
    """
    Get configuration values from command line arguments.
    """
    def __init__(self, argv=sys.argv):
        self.argv=argv

    def get(self, field, default=MISSING):
        raise NotImplementedError("CommandLineReader not yet implemented")


class DotEnvReader(Reader):
    """
    Get configuration values from a `.env` file.
    """
    def __init__(self, path='.env'):
        self.path = path
        self.canonical_kv_mapping = {}
        with open(self.path) as f:
            for line in f:
                try:
                    key, value = line.split("=", 1)
                except ValueError:
                    continue
                self.canonical_kv_mapping[key.upper()] = value


class IniFileReader(Reader):
    """
    Get configuration values from a `.ini` file.
    """
    def __init__(self, path, namespace="DEFAULT"):
        self.path = path
        self.namespace = namespace


class TomlFileReader(Reader):
    """
    Get configuration values from a `.toml` file.
    """

class JsonFileReader(Reader):
    """
    Get configuration values from a `.json` file.
    """
    def __init__(self, path, required=True):
        self.path = path
        with open(self.path) as f:
            self.canonical_kv_mapping = {k.upper(): v for k, v in json.load(f).items()}

class ConsulReader(Reader):
    """
    Get configuration values from a remote consul key value store.
    """
    def __init__(self, root, namespace=''):
        self.root = root
        self.namespace = namespace
        self.fetch_canonical_kv()

    def fetch_canonical_kv(self):
        url = f"{self.root.rstrip('/')}/v1/kv/{self.namespace}?recurse=true"
        response = requests.get(url, verify=False)
        self.canonical_kv_mapping = {}
        for entry in response.json():
            key = entry["Key"][len(self.namespace) + 1:].upper()
            if not key:
                continue
            value = entry["Value"]
            self.canonical_kv_mapping[key] = value

class AwsParameterStoreReader(Reader):
    """
    Get configuration values from a remote AWS Parameter.
    """


def configclass(_cls=None, *, readers=None):
    def wrap(cls):
        if readers is None:
            _readers = [EnvironmentReader()]
        else:
            _readers = readers
        return _process_config_class(cls, _readers)

    # Called with keyword args
    if _cls is None:
        return wrap

    # Called with defaults
    return wrap(_cls)

def _process_config_class(cls, readers):
    # datacls = dataclass(frozen=True)(cls)
    datacls = dataclass(cls)
    original_new_fn = datacls.__new__
    original_init_fn = datacls.__init__
    cls._enum_name_mappings = {}
    cls._enum_value_mappings = {}

    def __new__(cls):
        global _CONFIGURATION_SINGLETON
        if _CONFIGURATION_SINGLETON is None:
            _CONFIGURATION_SINGLETON = original_new_fn(cls)
            for name, field in cls.__dataclass_fields__.items():
                if issubclass(field.type, Enum):
                    variants_by_name = {}
                    variants_by_value = {variant.value: variant.value for variant in field.type}
                    for variant in field.type:
                        variants_by_name[variant.name.upper()] = variant.name
                        value = str(variant.value).upper()
                        variants_by_value[value] = variant.value
                    cls._enum_name_mappings[field.type] = variants_by_name
                    cls._enum_value_mappings[field.type] = variants_by_value
        return _CONFIGURATION_SINGLETON

    def __init__(self):
        global _CONFIGURATION_SINGLETON_INIT
        if not _CONFIGURATION_SINGLETON_INIT:
            self.readers = readers
            config_dict = self.config_dict_from_fields()
            original_init_fn(self, **config_dict)

            _CONFIGURATION_SINGLETON_INIT = True

    def config_dict_from_fields(self):
        config_dict = {}
        for name, field in self.__dataclass_fields__.items():
            raw_value = MISSING

            # Try to fetch the value from the various readers in order, breaking
            # after the first non-MISSING value
            for reader in self.readers:
                value = reader.get(name)
                if value is not MISSING:
                    raw_value = value
                    break

            if raw_value is MISSING:
                # raise ValueError(f"Could not find configuration value for {name}")
                continue
            if issubclass(field.type, Enum):
                upper_value = raw_value.upper()
                if upper_value in self._enum_name_mappings[field.type]:
                    value = self._enum_name_mappings[field.type][upper_value]
                elif upper_value in self._enum_value_mappings[field.type]:
                    value = self._enum_value_mappings[field.type][upper_value]
                else:
                    raise ValueError("SOMETHING SOMETHING")
            elif issubclass(field.type, bool):
                canonicalized_value = raw_value.upper()
                if canonicalized_value in ["TRUE", "1"]:
                    value = True
                elif canonicalized_value in ["FALSE", "0"]:
                    value = False
                else:
                    raise ValueError(f"{name} is not a valid boolean value")
            elif not (field.default is MISSING or isinstance(field.default, field.type)) and isinstance(field.default, FunctionType):
                # We have a converter function to use
                value = field.default(raw_value)
            else:
                value = field.type(raw_value)
            config_dict[name] = value
        print(config_dict)
        return config_dict


    datacls.__new__ = __new__
    datacls.__init__ = __init__
    datacls.config_dict_from_fields = config_dict_from_fields
    return datacls


class Environment(Enum):
    production = 0
    test = 1
    development = 2
    local = 3

class LogLevel(Enum):
    NotSet = logging.NOTSET
    Debug = logging.DEBUG
    Info = logging.INFO
    Warn = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL


def kv_list(str_value):
    return {item.split("=")[0]: item.split("=")[1] for item in str_value.split()}
