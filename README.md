# ConfigClasses

Think python's dataclasses module [PEP-557](https://www.python.org/dev/peps/pep-0557/) for configuration.
Pulls in configuration from various sources into a single integrated, global configuration
object. The configuration data can be reloaded on demand.


## Quickstart

```python
from configclasses import configclass, LogLevel, Environment

@configclass
class Configuration():
    ENVIRONMENT: Environment
    HOST: str
    PORT: int
    LOG_LEVEL: LogLevel
    DB_ADDRESS: str
    DB_PORT: int

config = Configuration()

# access fields by name
config.HOST == "localhost"

# Fields with `Enum` types will have variants as values
config.ENVIRONMENT == Environment.Development

# Reload config values from sources
config.reload()

# Configuration objects can now have different values
config.ENVIRONMENT == Environment.Production
```


## Features
  - Globally accessable configuration classes
  - Easily pull from many sources of configuration
  - Prioritize sources of configuration
  - Typed configuration values:
    - `Enum` types can be used to limit the values allowed
    - `converter` functions can turn stringly typed or primitive types into complex types such as dicts or classes


## TODO
  - [ ] Reload method
  - [ ] CLI source
  - [ ] Deal with sources that only provide stringly typed values and values that provide other primitives
  - [ ] Type converters
  - [ ] Multiple named configuration objects
  - [ ] Some sources might be case-insensitive.
  - [ ] Async/Sync versions of sources
  - [ ] Research and design push updates (as opposed to polling updates)
  - [ ] Comprehensive docs
         Includes docs on adding your own sources.


## Contribution

Feature requests, issues, and Pull Requests welcome.
Please file an issue with a feature request or suggestion intended to prompt discussion
before submitting a PR that implements new functionality to avoid writing code that
conflicts with the goals of the project.


## License

Licensor solely permits licensee to license under either of the following two options
 * Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you shall be dual licensed as above, without any
additional terms or conditions.
