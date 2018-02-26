import argparse
from enum import Enum
import json
import os
import sys
import configparser

from dataclasses import MISSING
import requests
import toml

from .conversions import quote_stripped

class Source:
    """
    Source knows how to get values out of a `canonical_kv_mapping` instance field
    or return a default
    """
    def namespace_stripped_key(self, key):
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

    def reload(self):
        """
        No-op reload for sources that don't have reload functionality.
        """


class EnvironmentSource(Source):
    """
    Get configuration values from case insensitive environment variables.
    """
    def __init__(self, namespace=None, environ=os.environ):
        self.namespace = namespace
        self.environ = environ
        self.reload()

    def reload(self):
        self.canonical_kv_mapping = {}
        for key, value in self.environ.items():
            key = self.namespace_stripped_key(key)
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
    Get configuration values from a `.env` file.
    """
    def __init__(self, path='.env', filehandle=None, namespace=None):
        super().__init__(path, filehandle, namespace)

    def canonical_from_filehandle(self, fh):
        self.canonical_kv_mapping = {}
        for line in fh.read().split("\n"):
            try:
                key, value = line.split("=", 1)
            except ValueError:
                continue
            key, value = key.strip(), value.strip()
            key = self.namespace_stripped_key(key)
            if key is not None:
                value = quote_stripped(value)
                self.canonical_kv_mapping[key] = value


class JsonSource(FileSource):
    """
    Get configuration values from a json encoded file or filehandle.
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
    Ini is case insensitive.
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
    Get configuration values from command line arguments.
    
    Optionally pass in a prexisting `argparse.ArgumentParser` instance to add
    to an existing set of command line arguments rather than only using auto-generated
    command line arguments.
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
    """
    def __init__(self, root, namespace="", http=requests):
        self.root = root.rstrip("/")
        self.namespace = namespace
        self.http = http
        self.reload()

    def reload(self):
        url = f"{self.root}/v1/kv/{self.namespace}?recurse=true"
        response = self.http.get(url)
        self.canonical_kv_mapping = {}
        for entry in response.json():
            key = entry["Key"][len(self.namespace) + 1:].upper()
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
