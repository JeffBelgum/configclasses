"""
Contains the configclass wrapper and the internal registry used to store
global configuration objects.
"""

from enum import Enum
from types import FunctionType

from dataclasses import dataclass, MISSING, Field as DField

from .conversions import EnumConversionRegistry, to_bool
from .sources import EnvironmentSource


# The global wrap registry is used to check whether a class has already been
# wrapped as a configclass.
# The global instance registry is used to enforce instances are only
# created and initialized once per configclass type and that subsequent
# instantiation returns the previously initialized singleton object
# The shape of the instance registry dict is {ClassType: [instance, initialized_bool_flag]}
_WRAP_REGISTRY = set()
_INSTANCE_REGISTRY = {}

class Field(DField):
    """
    Subclasses the `dataclasses.Field` type and adds a converter attribute.
    """
    def __init__(self, converter, default, default_factory, init, repr, hash, compare, metadata):
        super().__init__(default, default_factory, init, repr, hash, compare, metadata)
        self.converter = converter


def field(*, converter=None, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None):
    """
    factory function to create `Field` instances
    """
    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return Field(converter, default, default_factory, init, repr, hash, compare, metadata)


def configclass(_cls=None, *, sources=None):
    def wrap(cls):
        if sources is None:
            _sources = [EnvironmentSource()]
        else:
            _sources = sources
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
            kwargs = self.kwargs_from_fields()
            original_init_fn(self, **kwargs)

            initialized = True
            _INSTANCE_REGISTRY[cls][1] = initialized


    def kwargs_from_fields(self):
        kwargs = {}
        for name, field in self.__dataclass_fields__.items():
            value = MISSING

            # Try to fetch the value from the various sources in order, breaking
            # after the first non-MISSING value
            for source in self.sources:
                this_value = source.get(name)
                if this_value is not MISSING:
                    value = this_value
                    break

            if value is MISSING:
                # commented because default might exist for field:
                # raise ValueError(f"Could not find configuration value for {name}")
                continue

            kwargs[name] = self.convert_raw_value(field, value)

        return kwargs


    def convert_raw_value(self, field, raw_value):
        if issubclass(field.type, Enum):
            return self._enum_registry.to_enum(field.type, raw_value)
        elif issubclass(field.type, bool):
            return to_bool(raw_value)
        elif getattr(field, "converter", None) is not None:
            # We have a converter function to use
            return field.converter(raw_value)
        else:
            # Most primitive types handle conversions in the constructor.
            return field.type(raw_value)


    datacls.__new__ = __new__
    datacls.__init__ = __init__
    datacls.kwargs_from_fields = kwargs_from_fields
    datacls.convert_raw_value = convert_raw_value
    return datacls
