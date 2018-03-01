.. _guide:

User's Guide
============

Example::

    from configclasses import configclass, LogLevel, Environment
    
    # Wrap your configuration class in the `configclass` decorator
    # By default, it looks for matching variables in the environment.
    @configclass
    class Configuration:
        ENVIRONMENT: Environment    # Enum 
        LOG_LEVEL: LogLevel         # Enum
        HOST: str
        PORT: int
        DB_HOST: str = "localhost"  # Default when field not found
        DB_PORT: int = 5432         # Default when field not found
    
    # Instantiating a `Configuration` will always return the same object
    config = Configuration()
    
    # access fields by name
    config.HOST == "localhost"
    
    # `int` typed fields will be ints
    config.PORT == 8080
    
    # Fields with `Enum` types will have variants as values
    config.ENVIRONMENT == Environment.Development
    
    # Reload config values from sources
    config.reload()
    
    # Configuration objects can now have different values
    config.ENVIRONMENT == Environment.Production
    
    
    # Config classes can also be configured with other `sources`
    from configclasses.sources import DotEnvSource, EnvironmentSource
    
    @configclass(sources=[DotEnvSource(), EnvironmentSource()])
    class Configuration:
        HOST: str
        PORT: int
        DB_ADDRESS: str = "localhost"
        DB_PORT: int = 5432
        ENVIRONMENT: Environment
        LOG_LEVEL: LogLevel
    
    # First, a `.env` file will be searched for values, then
    # any values that are not present there will be searched
    # for in the program's environment.
    config = Configuration()

