import io
import json
from typing import Optional
from unittest.mock import MagicMock, mock_open, patch

import pytest
from dataclasses import MISSING

from configclasses import configclass
from configclasses.enums import Environment, LogLevel
from configclasses.sources import (
    CommandLineSource,
    ConsulSource,
    DotEnvSource,
    EnvironmentSource,
    IniSource,
    JsonSource,
    TomlSource,
)


def test_environment_source():
    environ = {"VAR1": "1", "var2": "2"}
    src = EnvironmentSource(environ=environ)

    assert src.get("VAR1") == "1"
    assert src.get("var2") == "2"
    assert src.get("var3", "3") == "3"

    assert src.get("Var1") is MISSING
    assert src.get("VAR2") is MISSING
    assert src.get("var3") is MISSING

def test_environment_source_reload():
    environ = {"VAR1": "1", "var2": "2"}
    src = EnvironmentSource(environ=environ)

    assert src.get("VAR1") == "1"
    assert src.get("VAR3") is MISSING

    environ["VAR1"] = "one"
    environ["VAR3"] = "three"
    src.reload()

    assert src.get("VAR1") == "one"
    assert src.get("VAR3") == "three"

def test_namespaced_environment_source():
    environ = {"JB_VAR1": "1", "VAR1": "not 1", "jb_VAR2": "2"}
    src = EnvironmentSource(namespace="JB_", environ=environ)
    assert src.get("VAR1") == "1"
    assert src.get("VAR2") is MISSING
    assert src.get("VAR2", "2") == "2"

@pytest.fixture
def dot_env_mock_data():
    return """\
HOST=hostname
PORT=9999
API_KEY="secret key"
ENVIRONMENT=LOCAL
LOG_LEVEL=info
DISTRIBUTED=FALSE
LOG_CONFIG='{"handler":"syslog"}'
USERS='master=admin slave=readonly'
AWS_SECRET_ACCESS_KEY='key from environ'
COMMON_KEY='environment common value'
"""

def test_default_dot_env_source(dot_env_mock_data):
    with patch('configclasses.sources.open', mock_open(read_data=dot_env_mock_data)) as m:
        src = DotEnvSource()
    m.assert_called_once_with('.env', 'rb')
    assert src.get("HOST") == "hostname"
    assert src.get("PORT") == "9999"
    assert src.get("host") is MISSING

def test_custom_path_dot_env_source(dot_env_mock_data):
    with patch('configclasses.sources.open', mock_open(read_data=dot_env_mock_data)) as m:
        src = DotEnvSource(path="custom_dot_env_path")
    m.assert_called_once_with('custom_dot_env_path', 'rb')
    assert src.get("HOST") == "hostname"
    assert src.get("PORT") == "9999"
    assert src.get("host") is MISSING

def test_namespaced_dot_env_source(dot_env_mock_data):
    with patch('configclasses.sources.open', mock_open(read_data=dot_env_mock_data)) as m:
        src = DotEnvSource(namespace="AWS_")
    m.assert_called_once_with('.env', 'rb')
    assert src.get("HOST") is MISSING
    assert src.get("SECRET_ACCESS_KEY") == "key from environ"

def test_json_source():
    # empty file
    filehandle = io.StringIO("")
    with pytest.raises(json.decoder.JSONDecodeError):
        JsonSource(filehandle=filehandle)

    # simple config
    string = json.dumps({"HOST": "localhost", "PORT": 8888})
    filehandle = io.StringIO(string)
    src = JsonSource(filehandle=filehandle)
    assert src.get("HOST") == "localhost"
    assert src.get("PORT") == 8888
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    # Bytes should work too
    string = json.dumps({"HOST": "localhost", "PORT": 8888})
    filehandle = io.BytesIO(string.encode())
    src = JsonSource(filehandle=filehandle)
    assert src.get("HOST") == "localhost"
    assert src.get("PORT") == 8888
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    filehandle = io.StringIO(string)
    with pytest.raises(ValueError):
        src = JsonSource(path='fake-path', filehandle=filehandle)
    with pytest.raises(ValueError):
        src = JsonSource()

def test_namespaced_json_source():
    # single nesting
    string = json.dumps({
        "APP-1": {"HOST": "app-1-localhost", "PORT": 1},
        "APP-2": {"HOST": "app-2-localhost", "PORT": 2},
    })
    filehandle = io.StringIO(string)
    src = JsonSource(filehandle=filehandle, namespace=["APP-1"])
    assert src.get("HOST") == "app-1-localhost"
    assert src.get("PORT") == 1
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    # deep nesting
    string = json.dumps({
        "APP-1": {
            "SERVICE-1": {
                "INSTANCE-1": {"HOST": "app-1-localhost", "PORT": 1},
                "INSTANCE-2": {},
            },
        },
        "APP-2": {"HOST": "app-2-localhost", "PORT": 2},
    })
    filehandle = io.StringIO(string)
    src = JsonSource(filehandle=filehandle, namespace=["APP-1", "SERVICE-1", "INSTANCE-1"])
    assert src.get("HOST") == "app-1-localhost"
    assert src.get("PORT") == 1
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    filehandle = io.StringIO(string)
    src = JsonSource(filehandle=filehandle, namespace=["APP-1", "SERVICE-1", "INSTANCE-2"])
    assert src.get("HOST") is MISSING
    assert src.get("HOST", default="DEFAULT") == "DEFAULT"

    with pytest.raises(KeyError):
        filehandle = io.StringIO(string)
        JsonSource(filehandle=filehandle, namespace=["APP-1", "SERVICE-2", "INSTANCE-2"])

def test_toml_source():
    string = """
    HOST = "top-level-host"
    PORT = 1

    [APP-1]
    HOST = "app-1-host"
    PORT = 2

    [APP-1.SERVICE-1.INSTANCE-1]
    HOST = "nested-host"
    PORT = 3

    [APP-2]
    HOST = "app-2-host"
    PORT = 4
    """

    filehandle = io.BytesIO(string.encode())
    with pytest.raises(ValueError):
        src = TomlSource(path='fake-path', filehandle=filehandle)
    with pytest.raises(ValueError):
        src = TomlSource()

    filehandle = io.BytesIO(string.encode())
    src = TomlSource(filehandle=filehandle)
    assert src.get("HOST") == "top-level-host"
    assert src.get("PORT") == 1
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    filehandle = io.BytesIO(string.encode())
    src = TomlSource(filehandle=filehandle, namespace=["APP-1"])
    assert src.get("HOST") == "app-1-host"
    assert src.get("PORT") == 2

    filehandle = io.BytesIO(string.encode())
    src = TomlSource(filehandle=filehandle, namespace=["APP-1", "SERVICE-1", "INSTANCE-1"])
    assert src.get("HOST") == "nested-host"
    assert src.get("PORT") == 3

    filehandle = io.BytesIO(string.encode())
    with pytest.raises(KeyError):
        TomlSource(filehandle=filehandle, namespace=["APP-3"])

def test_ini_source():
    string = """
    [DEFAULT]
    HOST = "default-host"
    PORT = 0

    [APP-1]
    HOST = "app-1-host"
    PORT = "1"

    [APP-2]
    HOST = "app-2-host"
    PORT = 2
    """

    filehandle = io.StringIO(string)
    with pytest.raises(ValueError):
        src = IniSource(path='fake-path', filehandle=filehandle)
    with pytest.raises(ValueError):
        src = IniSource()

    filehandle = io.StringIO(string)
    src = IniSource(filehandle=filehandle)
    assert src.get("HOST") == "default-host"
    assert src.get("PORT") == "0"
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    # Bytes do not work
    filehandle = io.BytesIO(string.encode())
    src = IniSource(filehandle=filehandle)
    assert src.get("HOST") == "default-host"
    assert src.get("PORT") == "0"
    assert src.get("MISSING") is MISSING
    assert src.get("MISSING", default="DEFAULT") == "DEFAULT"

    filehandle = io.StringIO(string)
    src = IniSource(filehandle=filehandle, namespace="APP-1")
    assert src.get("HOST") == "app-1-host"
    assert src.get("PORT") == "1"

    filehandle = io.StringIO(string)
    with pytest.raises(KeyError):
        IniSource(filehandle=filehandle, namespace="APP-3")


def test_cli_source():
    argv = [
        "--HOST", "localhost",
        "--PORT", "443",
        "--ENVIRONMENT", "Production",
    ]
    cli_src = CommandLineSource(argv=argv)

    with pytest.raises(RuntimeError):
        cli_src.get("HOST")

    @configclass(sources=[cli_src])
    class Configuration:
        ENVIRONMENT: Environment
        HOST: str
        PORT: int

    config = Configuration()
    assert config.HOST == "localhost"
    assert config.PORT == 443
    assert config.ENVIRONMENT == Environment.Production

def test_consul_source():
    # Mock data
    mock_consul_response = [
       {
           "LockIndex": 0,
           "Key": "test/namespace/HOST",
           "Flags": 0,
           "Value": "localhost",
           "CreateIndex": 000000,
           "ModifyIndex": 000000
       },
       {
           "LockIndex": 0,
           "Key": "test/namespace/PORT",
           "Flags": 0,
           "Value": 8080,
           "CreateIndex": 000000,
           "ModifyIndex": 000000
       },
       {
           "LockIndex": 0,
           "Key": "test/namespace/UNUSED",
           "Flags": 0,
           "Value": "unused value",
           "CreateIndex": 000000,
           "ModifyIndex": 000000
       },
       {
           "LockIndex": 0,
           "Key": "test/namespace/NULL",
           "Flags": 0,
           "Value": None,
           "CreateIndex": 000000,
           "ModifyIndex": 000000
       },
    ]
    response = MagicMock()
    response.json.return_value = mock_consul_response
    http = MagicMock()
    http.get.return_value = response

    # create and test source
    src = ConsulSource(root="http://fake-consul", namespace="test/namespace", http=http)
    assert src.get("HOST") == "localhost"
    assert src.get("PORT") == 8080
    assert src.get("NULL") == None
