"""
Contains the configclass wrapper and the internal registry used to store
global configuration objects.
"""

import re
from enum import Enum
from types import FunctionType
from typing import Any, Dict, Set, Tuple, Type

from dataclasses import MISSING
from dataclasses import Field as DField
from dataclasses import dataclass

from .conversions import EnumConversionRegistry, to_bool
from .sources import EnvironmentSource, FieldsDependentSource

# The global wrap registry is used to check whether a class has already been
# wrapped as a configclass.
# The global instance registry is used to enforce instances are only
# created and initialized once per configclass type and that subsequent
# instantiation returns the previously initialized singleton object
# The shape of the instance registry dict is {ClassType: [instance, initialized_bool_flag]}
_WRAP_REGISTRY: Set[Type] = set()
_INSTANCE_REGISTRY: Dict[Type, Tuple[Any, bool]] = {}

MISSING_ARGUMENTS_REGEX = re.compile(r"__init__\(\) missing (?P<nargs>\d+) required positional arguments?: (?P<names>.*)\Z")

class Field(DField):
    """
    Subclasses the `dataclasses.Field` type and adds a converter attribute.
    """
    def __init__(self, converter, validator, default, default_factory, init, repr, hash, compare, metadata):
        super().__init__(default, default_factory, init, repr, hash, compare, metadata)
        self.converter = converter
        self.validator = validator


def field(*, converter=None, validator=None, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None):
    """
    This function can be used if the field differs from the default functionality.
    It is the same as the field function in the dataclasses module except that it
    includes a ``converter`` argument that can be used to convert from a primitive
    type to a more complex type such as a dict or custom class.

    :param converter: is a function that takes a single argument and constructs a return value that is the same as the conficlass field's type annotation.
    :param converter: is a function that takes a single argument and returns True or False depending on whether that argument is considerd a valid value.
    :param default: is the default value of the field.
    :param default_factory: is a 0-argument function called to initialize a field's value.
    :param init: if True, the field will be a parameter to the class's __init__() function.
    :param repr: if True, the field will be included in the object's repr().
    :param hash: if True, the field will be included in the object's hash().
    :param compare: if True, the field will be used in comparison functions.
    :param metadata: if specified, must be a mapping which is stored but not otherwise examined by dataclass.

    :raises ValueError: It is an error to specify both default and default_factory.

    """
    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return Field(converter, validator, default, default_factory, init, repr, hash, compare, metadata)


def configclass(_cls=None, *, source=None, sources=None):
    """
    Turn a class into a configclass with the default EnvironmentSource used.

    For example, configuring the host and port for a web application might look
    like this:

    >>> from configclasses import configclass
    >>> @configclass
    ... class Configuration:
    ...     HOST: str
    ...     PORT: int

    Turn a class into a configclass using the user provided source or sources list.

    :param source: single ``Source`` used to fetch values.
    :param sources: list of ``Source`` used to fetch values, prioritized from first to last.

    :raises ValueError: The user must pass `either` the source `or` a list of sources. It is an error to provide both.

    Configuring the host and port for a web application using both command line arguments
    and environment variables as sources:

    >>> from configclasses import configclass, sources
    >>> env_source = EnvironmentSource()
    >>> cli_source = CommandLineSource()
    >>> @configclass(sources=[cli_source, env_source])
    ... class Configuration:
    ...     HOST: str
    ...     PORT: int

    Because the ``cli_source`` comes `after` the ``env_source`` in the list of ``sources``,
    it will be prioritized when fetching values that are found in both sources.

    Decorate your configuration classes with the `configclass` decorator to turn them into
    Configuration Classes.

    The returned configclass will have a ``.reload()`` method present, that can be used to
    reload values from configuration sources on demand. This reload affects `all` instances
    of the configclass you are reloading.
    """
    def wrap(cls):
        if source is not None and sources is not None:
            raise ValueError("Cannot pass both `source` and `sources` to configclass decorator. Pass one or the other.")
        if source is not None:
            _sources = [source]
        elif sources is not None:
            _sources = sources
        else:
            _sources = [EnvironmentSource()]
        return _process_config_class(cls, _sources)

    # Called with keyword args
    if _cls is None:
        return wrap

    # Called with defaults
    return wrap(_cls)

def _process_config_class(cls, sources):
    global _WRAP_REGISTRY
    if cls in _WRAP_REGISTRY:
        raise RuntimeError("Cannot double register a class as a `configclass`")
    _WRAP_REGISTRY.add(cls)

    datacls = dataclass(cls)
    original_new_fn = datacls.__new__
    original_init_fn = datacls.__init__
    cls._enum_registry = EnumConversionRegistry()

    def __new__(cls):
        global _INSTANCE_REGISTRY
        if cls not in _INSTANCE_REGISTRY:
            initialized = False
            _INSTANCE_REGISTRY[cls] = [original_new_fn(cls), initialized]

            # Do any preprocessing needed based on field types
            for name, field in cls.__dataclass_fields__.items():
                if issubclass(field.type, Enum):
                    cls._enum_registry.add_enum(field.type)

        return _INSTANCE_REGISTRY[cls][0]


    def __init__(self):
        global _INSTANCE_REGISTRY
        cls = type(self)
        if not _INSTANCE_REGISTRY[cls][1]:
            self.sources = sources

            # provide configclass fields to sources that need them to work properly
            for source in self.sources:
                if isinstance(source, FieldsDependentSource):
                    source.update_with_fields(cls.__dataclass_fields__)

            kwargs = self.kwargs_from_fields()
            try:
                original_init_fn(self, **kwargs)
            except TypeError as exc:
                match = MISSING_ARGUMENTS_REGEX.match(str(exc))
                if match is not None:
                    nargs = int(match.group("nargs"))
                    names = match.group("names")
                    field_fields = "fields" if nargs > 1 else "field"
                    raise ValueError(f"'{type(self).__name__}' is missing {nargs} required configuration {field_fields}: {names}")
                else:
                    raise

            initialized = True
            _INSTANCE_REGISTRY[cls][1] = initialized


    def kwargs_from_fields(self):
        kwargs = {}
        for name, field in self.__dataclass_fields__.items():
            value = MISSING

            # Try to fetch the value from the various sources in right-to-left order,
            # breaking after the first non-MISSING value
            for source in reversed(self.sources):
                this_value = source.get(name)
                if this_value is not MISSING:
                    value = this_value
                    break

            if value is MISSING:
                # commented because default might exist for field:
                # raise ValueError(f"Could not find configuration value for {name}")
                continue

            value = self.convert_raw_value(field, value)
            if getattr(field, 'validator', None):
                try:
                    if callable(field.validator):
                        if not field.validator(value):
                            raise ValueError(f"Value fails validation function")
                    elif value not in field.validator:
                        raise ValueError(f"Value fails validation function")
                except TypeError as exc:
                    raise TypeError("Bad validation function") from exc
            kwargs[name] = value

        return kwargs


    def convert_raw_value(self, field, raw_value):
        if issubclass(field.type, Enum):
            return self._enum_registry.to_enum(field.type, raw_value)
        elif issubclass(field.type, bool):
            return to_bool(raw_value)
        elif getattr(field, "converter", None) is not None:
            # We have a converter function to use
            value = field.converter(raw_value)
            if not isinstance(value, field.type):
                raise TypeError("Custom converter function did not produce the required type")
            return value
        else:
            # Most primitive types handle conversions in the constructor.
            return field.type(raw_value)

    def reload(self):
        """
        Reload all sources and then re-init self.
        """
        for source in self.sources:
            source.reload()

        global _INSTANCE_REGISTRY
        cls = type(self)
        _INSTANCE_REGISTRY[cls][1] = False
        self.__init__()

    datacls.__new__ = __new__
    datacls.__init__ = __init__
    datacls.kwargs_from_fields = kwargs_from_fields
    datacls.convert_raw_value = convert_raw_value
    datacls.reload = reload

    return datacls
