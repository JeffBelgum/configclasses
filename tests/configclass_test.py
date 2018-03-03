import io
import json

import pytest

from configclasses import configclass, Environment, LogLevel, EnvironmentSource, JsonSource, field, kv_list


# TODO: Test of all config sources with interactions, None types, 
#       missing types, conflicting types, order of precidence,
#       sources that cannot be reached.


def test_empty_configclass_with_default_readers():
    @configclass
    class Configuration:
        pass

    config_1 = Configuration()
    config_2 = Configuration()
    config_3 = Configuration()
    assert config_1 is config_2 is config_3


def test_double_register_configclass():
    @configclass
    class Configuration:
        pass

    with pytest.raises(RuntimeError):
        # cannot double register a configclass
        configclass(Configuration)


def test_basic_configclass_with_env_reader():
    env_src = EnvironmentSource(environ={
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "info",
        "HOST": "localhost",
        "PORT": "8080",
        "API_KEY": "secret api key",
        "DISTRIBUTED": "FALSE",
    })

    @configclass(sources=[env_src])
    class Configuration:
        ENVIRONMENT: Environment
        LOG_LEVEL: LogLevel
        HOST: str
        PORT: int
        API_KEY: str
        DISTRIBUTED: bool

    config = Configuration()
    assert config.ENVIRONMENT == Environment.Test
    assert config.LOG_LEVEL == LogLevel.Info
    assert config.HOST == "localhost"
    assert config.PORT == 8080
    assert config.API_KEY == "secret api key"
    assert config.DISTRIBUTED == False


def test_basic_configclass_with_multiple_readers():
    env_src = EnvironmentSource(environ={
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "info",
        "HOST": "localhost",
        "PORT": "8080",
        "API_KEY": "secret api key",
        "DISTRIBUTED": "FALSE",
    })

    # single nesting
    json_str = json.dumps({
        "APP-1": {"HOST": "app-1-localhost", "PORT": 1234},
        "APP-2": {"HOST": "app-2-localhost", "PORT": 5678},
    })
    json_src = JsonSource(filehandle=io.StringIO(json_str), namespace=["APP-1"])

    # json_src values take precidence over env_src values
    @configclass(sources=[json_src, env_src])
    class Configuration:
        ENVIRONMENT: Environment
        LOG_LEVEL: LogLevel
        HOST: str
        PORT: int
        API_KEY: str
        DISTRIBUTED: bool

    config = Configuration()
    assert config.ENVIRONMENT == Environment.Test
    assert config.LOG_LEVEL == LogLevel.Info
    assert config.HOST == "app-1-localhost"
    assert config.PORT == 1234
    assert config.API_KEY == "secret api key"
    assert config.DISTRIBUTED == False


def test_basic_configclass_with_missing_values():
    env_src = EnvironmentSource(environ={
        "HOST": "localhost",
    })

    @configclass(sources=[env_src])
    class Configuration:
        HOST: str
        PORT: int

    with pytest.raises(ValueError):
        config = Configuration()


def test_converter_configclass():
    json_field = {"a": 1, "b": 2}
    kv_field = {"c": "3", "d": "4"}
    env_src = EnvironmentSource(environ={
        "JSON_FIELD": json.dumps(json_field),
        "KV_FIELD": ",".join(f"{k}={v}" for k, v in kv_field.items()),
    })

    @configclass(sources=[env_src])
    class Configuration:
        JSON_FIELD: dict = field(converter=json.loads)
        KV_FIELD: dict = field(converter=kv_list)

    config = Configuration()
    assert config.JSON_FIELD == json_field
    assert config.KV_FIELD == kv_field


def test_configclass_with_defaults():
    env_src = EnvironmentSource(environ={})

    @configclass(sources=[env_src])
    class Configuration:
        INT_FIELD: int = 1
        STRING_FIELD: str = "default string"

    config = Configuration()
    assert config.INT_FIELD == 1
    assert config.STRING_FIELD == "default string"


def test_basic_configclass_reload():
    environ = {
        "HOST": "localhost",
    }
    env_src = EnvironmentSource(environ=environ)

    @configclass(sources=[env_src])
    class Configuration:
        HOST: str

    config = Configuration()
    assert config.HOST == "localhost"
    environ["HOST"] = "newhost"
    assert config.HOST == "localhost"
    config.reload()
    assert config.HOST == "newhost"
