"""
Functions and classes for converting from one type to another.

Some are useful only internally, others have utility outside of
the internals of configclasses. See the documentation for
conversions considered useful to api consumers.
"""

from decimal import Decimal
from typing import Union

T = Union[bool, str, bytes, bytearray, int, float, Decimal]

def to_bool(value: T) -> bool:
    """
    Convert a bool, string type or numeric type to a bool.

    raises: ValueError on invalid values
            TypeError on invalid `value` types.
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        upper = value.upper()
        if upper in ["TRUE", "1"]:
            return True
        elif upper in ["FALSE", "0"]:
            return False
        else:
            # TODO tell the user what field this is
            raise ValueError(f"{value} is not a valid boolean value")
    elif isinstance(value, (bytes, bytearray)):
        upper_b = value.upper()
        if upper_b in [b"TRUE", b"1"]:
            return True
        elif upper_b in [b"FALSE", b"0"]:
            return False
        else:
            # TODO tell the user what field this is
            raise ValueError(f"{value} is not a valid boolean value")
    elif isinstance(value, (int, float, Decimal)):
        if value == 0:
            return False
        elif value == 1:
            return True
        else:
            raise ValueError(f"{value} is not a valid boolean value")
    raise TypeError(f"{type(value)} cannot be converted to a bool")


class EnumConversionRegistry():
    def __init__(self):
        self.name_mappings = {}
        self.value_mappings = {}

    def add_enum(self, enum):
        self.value_mappings[enum] = {variant.value: variant.value for variant in enum}

        variants_by_name = {}
        for variant in enum:
            variants_by_name[variant.name.upper()] = variant.name
            value = str(variant.value).upper()
            self.value_mappings[enum][value] = variant.value
        self.name_mappings[enum] = variants_by_name

    def to_enum(self, enum, raw_value):
        if not (enum in self.name_mappings and enum in self.value_mappings):
            raise ValueError(f"Enum type {enum} not registered")
        # Uppercase string type raw values
        if isinstance(raw_value, (str, bytes, bytearray)):
            canonical = raw_value.upper()
        else:
            canonical = raw_value

        if canonical in self.name_mappings[enum]:
            name = self.name_mappings[enum][canonical]
            return enum[name]
        elif canonical in self.value_mappings[enum]:
            value = self.value_mappings[enum][canonical]
            return enum(value)
        else:
            raise ValueError(f"Invalid value {raw_value} for Enum {enum}")


def quote_stripped(value: str) -> str:
    """
    Strip out a single level of single (') or double (") quotes.
    """
    single, double = "'", '"'
    if (value.startswith(single) and value.endswith(single)) or\
       (value.startswith(double) and value.endswith(double)):
        return value[1:-1]
    return value


def csv_pairs(value: str) -> dict:
    """
    Kv lists are comma separated pairs of values where a pair is defined as
    ``"key=value"``. Whitespace around a key or value is stripped unless
    text is quoted. Empty pairs are skipped.

    :raises ValueError: on a malformed key value pair.

    An example usage:

    >>> csv_pairs("a=1,b=2")
    {"a": "1", "b": "2"}

    Typically it is used in specifying a configclass:

    >>> @configclass
    ... class Configuration:
    ...     PAIRS: dict = field(converter=csv_pairs)

    Then a string of key=value pairs will be converted into a dictionary
    in the ``Configuration`` class.
    """
    kv = {}
    for pair in value.split(","):
        if not pair.strip():
            continue  # Skip empty pairs
        # TODO: Raise more helpful exception on bad split
        key, val = pair.split("=", 1)
        key, val = key.strip(), val.strip()
        key, val = quote_stripped(key), quote_stripped(val)
        kv[key] = val

    return kv

def csv_list(value: str) -> list:
    """
    csv_lists are comma separated values. Whitespace around a value is stripped
    unless text is quoted. Empty values are skipped.

    An example usage:

    >>> csv_list("a,b,c")
    ["a", "b", "c"]

    Typically it is used in specifying a configclass:

    >>> @configclass
    ... class Configuration:
    ...     LIST: list = field(converter=csv_list)

    Then a string of values will be converted into a list of strings
    in the ``Configuration`` class.
    """
    return [quote_stripped(elem.strip()) for elem in value.split(",") if elem.strip()]
