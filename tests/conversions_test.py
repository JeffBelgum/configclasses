from decimal import Decimal
from enum import Enum

import pytest

from configclasses.conversions import EnumConversionRegistry, csv_list, csv_pairs, to_bool


@pytest.mark.parametrize("input, expected", [
    (False,               False),
    ("0",                 False),
    ("False",             False),
    ("FALSE",             False),
    ("false",             False),
    (b"False",            False),
    (bytearray(b"False"), False),
    (0,                   False),
    (0.0,                 False),
    (Decimal(0),          False),
    (True,                True),
    ("1",                 True),
    ("True",              True),
    ("TRUE",              True),
    ("true",              True),
    (b"True",             True),
    (bytearray(b"true"),  True),
    (1,                   True),
    (1.0,                 True),
    (Decimal(1),          True),
])
def test_to_bool(input, expected):
    assert to_bool(input) == expected
    
@pytest.mark.parametrize("input, expected", [
    ({},     TypeError),
    ([],     TypeError),
    (None,   TypeError),
    ("-1",   ValueError),
    ("2",    ValueError),
    ("t",    ValueError),
    ("",     ValueError),
    (b"",    ValueError),
    (-1,     ValueError),
    (-1.0,   ValueError),
    (1000,   ValueError),
    (0.0001, ValueError),
])
def test_to_bool_exceptions(input, expected):
    with pytest.raises(expected):
        to_bool(input)

def test_csv_pairs_conversion():
    actual = csv_pairs("a=1, b= 2 , c = 'this that',  d_key=d values=c,")
    expected = {"a": "1", "b": "2", "c": "this that", "d_key": "d values=c"}
    assert actual == expected

def test_csv_pairs_conversion():
    actual = csv_list("a, b, c,  d , ' e  ',")
    expected = ["a", "b", "c", "d", " e  "]
    assert actual == expected

# Enums and fixtures for testing EnumConversionRegistry
class Color(Enum):
    Red = 0
    Green = 1
    Blue = 2

class Size(Enum):
    Small = "s"
    Medium = "m"
    Large = "l"

class UnregisteredEnum(Enum):
    unused = 0
    values = 1

@pytest.fixture
def enum_registry():
    registry = EnumConversionRegistry()
    registry.add_enum(Color)
    registry.add_enum(Size)
    return registry

@pytest.mark.parametrize("enum, raw, expected", [
    (Color, "red", Color.Red),
    (Color, "Green", Color.Green),
    (Color, "BLUE", Color.Blue),
    (Color, 0, Color.Red),
    (Color, 2, Color.Blue),
    (Size, "small", Size.Small),
    (Size, "Medium", Size.Medium),
    (Size, "LARGE", Size.Large),
    (Size, "s", Size.Small),
    (Size, "l", Size.Large),
    (Size, "L", Size.Large),
])
def test_enum_conversion_registry(enum_registry, enum, raw, expected):
    assert enum_registry.to_enum(enum, raw) == expected


@pytest.mark.parametrize("enum, raw", [
    (Color, None),
    (Color, ""),
    (Color, "r"),
    (Color, "redd"),
    (Color, "redgreen"),
    (Color, -1),
    (Color, 3),
    (Size, ""),
    (Size, 0),
    (UnregisteredEnum, None),
    (UnregisteredEnum, "unused"),
    (UnregisteredEnum, 1),
])
def test_enum_conversion_registry_bad_values(enum_registry, enum, raw):
    with pytest.raises(ValueError):
        assert enum_registry.to_enum(enum, raw)
