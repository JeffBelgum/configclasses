from dataclasses import MISSING
import json
import toml
import os
import sys
import configparser

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


class EnvironmentSource(Source):
    """
    Get configuration values from case insensitive environment variables.
    """
    def __init__(self, namespace=None, environ=os.environ):
        self.namespace = namespace
        self.canonical_kv_mapping = {}
        for key, value in environ.items():
            key = self.namespace_stripped_key(key)
            if key is not None:
                value = quote_stripped(value)
                self.canonical_kv_mapping[key] = value


class DotEnvSource(Source):
    """
    Get configuration values from a `.env` file.
    """
    def __init__(self, path='.env', namespace=None):
        self.path = path
        self.namespace = namespace
        self.canonical_kv_mapping = {}
        with open(self.path) as f:
            for line in f.read().split("\n"):
                try:
                    key, value = line.split("=", 1)
                except ValueError:
                    continue
                key, value = key.strip(), value.strip()
                key = self.namespace_stripped_key(key)
                if key is not None:
                    value = quote_stripped(value)
                    self.canonical_kv_mapping[key] = value


class JsonSource(Source):
    """
    Get configuration values from a json encoded file or filehandle.
    """
    def __init__(self, path=None, filehandle=None, namespace=None):
        self.path = path
        self.filehandle = filehandle
        self.namespace = namespace
        if self.path is not None and self.filehandle is not None:
            raise ValueError("Cannot pass both path and filehandle. Try passing one or the other.")
        elif self.path is None and self.filehandle is None:
            raise ValueError("Either path or filehandle argument must be passed.")
        if self.path:
            with open(self.path) as fh:
                self.canonical_from_filehandle(fh)
        else:
            self.canonical_from_filehandle(self.filehandle)

    def canonical_from_filehandle(self, fh):
        obj = json.load(fh)
        if self.namespace is None:
            namespace = []
        else:
            namespace = self.namespace

        for ns in namespace:
            obj = obj[ns]

        self.canonical_kv_mapping = {k: v for k, v in obj.items()}


class TomlSource(Source):
    """
    Get configuration values from a `.toml` file.
    """
    def __init__(self, path=None, filehandle=None, namespace=None):
        self.path = path
        self.filehandle = filehandle
        self.namespace = namespace
        if self.path is not None and self.filehandle is not None:
            raise ValueError("Cannot pass both path and filehandle. Try passing one or the other.")
        elif self.path is None and self.filehandle is None:
            raise ValueError("Either path or filehandle argument must be passed.")
        if self.path:
            with open(self.path) as fh:
                self.canonical_from_filehandle(fh)
        else:
            self.canonical_from_filehandle(self.filehandle)

    def canonical_from_filehandle(self, fh):
        obj = toml.load(fh)
        if self.namespace is None:
            namespace = []
        else:
            namespace = self.namespace

        for ns in namespace:
            obj = obj[ns]

        self.canonical_kv_mapping = {k: v for k, v in obj.items()}


class IniSource(Source):
    """
    Get configuration values from a `.ini` file.
    Ini is case insensitive.
    """
    def __init__(self, path=None, filehandle=None, namespace=None):
        self.path = path
        self.filehandle = filehandle
        self.namespace = namespace
        if self.path is not None and self.filehandle is not None:
            raise ValueError("Cannot pass both path and filehandle. Try passing one or the other.")
        elif self.path is None and self.filehandle is None:
            raise ValueError("Either path or filehandle argument must be passed.")
        if self.path:
            with open(self.path) as fh:
                self.canonical_from_filehandle(fh)
        else:
            self.canonical_from_filehandle(self.filehandle)

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



# class ConsulSource(Source):
#     """
#     Get configuration values from a remote consul key value store.
#     """
#     def __init__(self, root, namespace=''):
#         self.root = root
#         self.namespace = namespace
#         self.fetch_canonical_kv()
# 
#     def fetch_canonical_kv(self):
#         url = f"{self.root.rstrip('/')}/v1/kv/{self.namespace}?recurse=true"
#         response = requests.get(url, verify=False)
#         self.canonical_kv_mapping = {}
#         for entry in response.json():
#             key = entry["Key"][len(self.namespace) + 1:].upper()
#             if not key:
#                 continue
#             value = entry["Value"]
#             self.canonical_kv_mapping[key] = value
# 
#
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
# 
# class CommandLineSource(Source):
#     """
#     Get configuration values from command line arguments.
#     """
