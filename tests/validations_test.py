import pytest

from configclasses import configclass, field
from .test_helpers import DictSource


@pytest.mark.parametrize("value", [ 0, 1, 2])
def test_iterator_validation_passes(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=range(3))
    config = Config()
    config.FIELD == value

@pytest.mark.parametrize("value", [ -1, 3])
def test_iterator_validation_fails(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=range(3))
    with pytest.raises(ValueError):
        config = Config()

@pytest.mark.parametrize("value", [ 1, 3, 4])
def test_list_validation_passes(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=[1, 3, 4])
    config = Config()
    config.FIELD == value

@pytest.mark.parametrize("value", [ 0, 2, 5])
def test_list_validation_fails(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=[1, 3, 4])
    with pytest.raises(ValueError):
        config = Config()

@pytest.mark.parametrize("value", [ 'a', 'cd'])
def test_string_validation_passes(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: str = field(validator="abcd")
    config = Config()
    config.FIELD == value

@pytest.mark.parametrize("value", [ 'abcde', 'z'])
def test_string_validation_fails(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: str = field(validator="abcd")
    with pytest.raises(ValueError):
        config = Config()

@pytest.mark.parametrize("value", [ 0, 2, 4])
def test_lambda_validation_passes(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=lambda x: x % 2 == 0)
    config = Config()
    config.FIELD == value

@pytest.mark.parametrize("value", [ 1, 3, -1])
def test_lambda_validation_fails(value):
    @configclass(source=DictSource(FIELD=value))
    class Config:
        FIELD: int = field(validator=lambda x: x % 2 == 0)
    with pytest.raises(ValueError):
        config = Config()

def test_invalid_validation_object():
    @configclass(source=DictSource(FIELD=1))
    class Config:
        FIELD: int = field(validator=1)
    with pytest.raises(TypeError):
        config = Config()
