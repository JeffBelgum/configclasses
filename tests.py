import json
from typing import Optional

from dataclasses import MISSING

from config import DotEnvReader, EnvironmentReader, configclass, Environment, LogLevel, kv_list, ConsulReader, JsonFileReader

import requests
requests.urllib3.disable_warnings()

def test_environment_reader():
    environ = {"VAR1": 1, "Var2": 2}
    env_rdr = EnvironmentReader(environ=environ)
    assert env_rdr.get("VAR1") == 1
    assert env_rdr.get("Var1") == 1
    assert env_rdr.get("VAR2") == 2
    assert env_rdr.get("var2") == 2
    assert env_rdr.get("var3") is MISSING
    assert env_rdr.get("var3", 3) == 3

def test_namespaced_environment_reader():
    environ = {"JB_VAR1": 1, "jb_Var2": 2}
    ns_env_rdr = EnvironmentReader(namespace="JB_", environ=environ)
    assert ns_env_rdr.get("VAR1") == 1
    assert ns_env_rdr.get("Var1") == 1
    assert ns_env_rdr.get("VAR2") == 2
    assert ns_env_rdr.get("var2") == 2
    assert ns_env_rdr.get("var3") is MISSING
    assert ns_env_rdr.get("var3", 3) == 3

def test_configclass_explicit_readers():
    readers = [
        # ConsulReader('https://consul-infra.ptera.org', 'infra/ops-metrics'),
        EnvironmentReader(),
        DotEnvReader(),
        JsonFileReader('env.json'),
    ]
    @configclass(readers=readers)
    class Configuration:
        JSON_KEY: str
        common_key: str
        ENVIRONMENT: Environment
        LOG_LEVEL: LogLevel
        host: str
        port: int
        api_key: str
        distributed: bool
        log_config: dict = json.loads
        users: dict = kv_list
        aws_access_key_id: str = None
        aws_secret_access_key: str = None

    print(Configuration())
    config = Configuration()

    config.JSON_KEY
    config.ENVIRONMENT

def test_configclass_default_readers():
    @configclass
    class Configuration:
        environment: Environment
        log_level: LogLevel
        host: str
        port: int
        api_key: str
        distributed: bool
        log_config: dict = json.loads
        users: dict = kv_list

    print(Configuration())
