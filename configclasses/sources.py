"""
`Source` classes know how to fetch configuration values from all kinds of different sources
of configuration values. A number of Source classes are provided by the library, and users
can implement their own sources.

TODO: link to documentation on implementing custom sources.

**Builtin sources:**
"""

import argparse
import configparser
import json
import os
import sys
from enum import Enum

import requests
import toml
from dataclasses import MISSING

from .conversions import quote_stripped


class Source:
    """
    Base class that all sources should inherit from.
    """
    def _namespace_stripped_key(self, key):
        """
        Strips a namespace from a key when the namespace simply prepends the key.
        """
        if self.namespace is None:
            return key
        if key.startswith(self.namespace):
            return key[len(self.namespace):]
        return None

    def get(self, field, default=MISSING):
        value = self.canonical_kv_mapping.get(field, MISSING)
        if value is MISSING:
            return default
        return value


class EnvironmentSource(Source):
    """
    Get configuration values from case insensitive environment variables.

    :param namespace: An optional string prefix to match on with environment variables.
    :param environ: A different source of environment variables can be passed if you don't want to use os.environ.

    If ``namespace`` is provided, only environment variable names that start with
    the namespace value will be considered. The namespace is also stripped off
    the variable name before it is stored.
    """
    def __init__(self, namespace=None, environ=os.environ):
        self.namespace = namespace
        self.environ = environ
        self.reload()

    def reload(self):
        """
        Fetch and parse values from the environment dict and store them.
        """
        self.canonical_kv_mapping = {}
        for key, value in self.environ.items():
            key = self._namespace_stripped_key(key)
            if key is not None:
                value = quote_stripped(value)
                self.canonical_kv_mapping[key] = value


class FileSource(Source):
    def __init__(self, path=None, filehandle=None, namespace=None):
        self.path = path
        self.filehandle = filehandle
        self.namespace = namespace
        self.filestart = None
        if self.filehandle and self.filehandle.seekable():
            filestart = self.filehandle.tell()
        self.reload()

    def reload(self):
        """
        Fetch and parse values from the file source and store them.

        If a ``path`` was provided to the source, the path will be reopened and read.
        If a ``filehandle`` was provided and the handle supports seeking, it will
        seek to the position the handle was at when passed to the source. If it
        does not support seeking, it will attempt to read from the current position.

        `It is up to the user to ensure that filehandles will act correctly given the above rules`
        """
        if self.path is not None and self.filehandle is not None:
            raise ValueError("Cannot pass both path and filehandle. Try passing one or the other.")
        elif self.path is None and self.filehandle is None:
            raise ValueError("Either path or filehandle argument must be passed.")
        if self.path:
            with open(self.path) as fh:
                self.canonical_from_filehandle(fh)
        else:
            if self.filestart is not None:
                self.filehandle.seek(self.filestart)
            self.canonical_from_filehandle(self.filehandle)


class DotEnvSource(FileSource):
    """
    Get configuration values from a `.env` (dotenv) formatted file.

    :param path: path to read from.
    :param filehandle: open file handle to read from.
    :param namespace: string prefix for values this sources will fetch from.

    :raises ValueError: It is an error if both ``path`` and ``filehandle`` are defined `or` neither ``path`` nor ``filehandle`` are defined.
    """
    def __init__(self, path=".env", filehandle=None, namespace=None):
        super().__init__(path, filehandle, namespace)

    def canonical_from_filehandle(self, fh):
        self.canonical_kv_mapping = {}
        for line in fh.read().split("\n"):
            try:
                key, value = line.split("=", 1)
            except ValueError:
                continue
            key, value = key.strip(), value.strip()
            key = self._namespace_stripped_key(key)
            if key is not None:
                value = quote_stripped(value)
                self.canonical_kv_mapping[key] = value


class JsonSource(FileSource):
    """
    Get configuration values from a json encoded file or filehandle.

    :param path: path to read from.
    :param filehandle: open file handle to read from.
    :param namespace: list of keys or indices used to access a nested configuration object.

    :raises ValueError: It is an error if both ``path`` and ``filehandle`` are defined `or` neither ``path`` nor ``filehandle`` are defined.

    Namespacing for json sources is best described by example:

    >>> json_value = \""" {
    ...     "nested": {
    ...         "configuration": {
    ...             "FOO": "foo_value",
    ...             "BAR": "bar_value",
    ...         }
    ...     }
    ... }\"""
    >>> namespace = ["nested", "configuration"]

    A ``JsonSource`` that reads a file with the contents of ``json_value`` with the ``namespace`` defined above
    would only consider the keys "FOO" and "BAR" as configuration values in scope.
    """
    def canonical_from_filehandle(self, fh):
        obj = json.load(fh)
        if self.namespace is None:
            namespace = []
        else:
            namespace = self.namespace

        for ns in namespace:
            obj = obj[ns]

        self.canonical_kv_mapping = {k: v for k, v in obj.items()}


class TomlSource(FileSource):
    """
    Get configuration values from a `.toml` file.

    :param path: path to read from.
    :param filehandle: open file handle to read from.
    :param namespace: optional list of nested section to search for configuration fields

    :raises ValueError: It is an error if both ``path`` and ``filehandle`` are defined `or` neither ``path`` nor ``filehandle`` are defined.
    """
    def canonical_from_filehandle(self, fh):
        obj = toml.load(fh)
        if self.namespace is None:
            namespace = []
        else:
            namespace = self.namespace

        for ns in namespace:
            obj = obj[ns]

        self.canonical_kv_mapping = {k: v for k, v in obj.items()}


class IniSource(FileSource):
    """
    Get configuration values from a `.ini` file.

    :param path: path to read from.
    :param filehandle: open file handle to read from.
    :param namespace: optional section to search for configuration fields

    :raises ValueError: It is an error if both ``path`` and ``filehandle`` are defined `or` neither ``path`` nor ``filehandle`` are defined.

    `Note: Python ini parsing is case insensitive.`
    """
    def canonical_from_filehandle(self, fh):
        config = configparser.ConfigParser()
        config.read_file(fh)
        if self.namespace:
            try:
                self.canonical_kv_mapping = {k.upper(): quote_stripped(v) for k, v in config.items(self.namespace)}
            except configparser.NoSectionError:
                raise KeyError(f"Namespace {self.namespace} missing")
        else:
            self.canonical_kv_mapping = {k.upper(): quote_stripped(v) for k, v in config.defaults().items()}

    def get(self, field, default=MISSING):
        return super().get(field.upper(), default)


class FieldsDependentSource(Source):
    """
    Source that requires the configclass pass in the fields that it knows about
    before any calls to get.
    """
    def get(self, field, default=MISSING):
        if not hasattr(self, "canonical_kv_mapping"):
            raise RuntimeError("Source must be provided with configclass source before values can be accessed")
        return super().get(field, default)


class CommandLineSource(FieldsDependentSource):
    """
    Get configuration values from command line arguments. Adds command line arguments
    for each field in the associated configclass.

    :param argparse: Optionally pass in a preexisting `argparse.ArgumentParser` instance to add to an existing set of command line arguments rather than only using auto-generated command line arguments.
    :param argv: Optionally pass a custom argv list. Most useful for testing.
    """
    def __init__(self, argparse=None, argv=sys.argv):
        self.parser = argparse
        self.argv = argv

    def update_with_fields(self, fields):
        if self.parser is None:
            self.parser = argparse.ArgumentParser()

        names = set()
        for name, field in fields.items():
            names.add(name)
            if issubclass(field.type, Enum):
                choices = [variant.name for variant in field.type]
            else:
                choices = None
            if issubclass(field.type, (int, float)):
                _type = field.type
            else:
                _type = str

            self.parser.add_argument(f"--{name}", choices=choices, type=_type)

        args = self.parser.parse_args(self.argv)

        self.canonical_kv_mapping = {}
        for key, value in vars(args).items():
            if key not in names:
                continue
            self.canonical_kv_mapping[key] = value


class ConsulSource(Source):
    """
    Get configuration values from a remote consul key value store.

    :param root: The address of the consul api to use. Don't forget to include the scheme (http or https)!
    :param namespace: The consul kv namespace from which to fetch fields.
    :param http: http library used to make get requests. Defaults to using requests.
    """
    def __init__(self, root, namespace=None, http=requests):
        self.root = root.rstrip("/")
        self.namespace = namespace
        self.http = http
        self.reload()

    def reload(self):
        namespace = "" if self.namespace is None else self.namespace
        url = f"{self.root}/v1/kv/{namespace}?recurse=true"
        response = self.http.get(url)
        self.canonical_kv_mapping = {}
        for entry in response.json():
            key = entry["Key"][len(namespace) + 1:].upper()
            if not key:
                continue
            value = entry["Value"]
            self.canonical_kv_mapping[key] = value


# class AwsParameterStoreSource(Source):
#     """
#     Get configuration values from a remote AWS Parameter.
#     """
#
#
# class EtcdSource(Source):
#     """
#     Get configuration values from etcd key value store.
#     """
#
# class RedisSource(Source):
#     """
#     Get configuration values from a redis key value store.
#     """
