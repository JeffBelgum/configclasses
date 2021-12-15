.. _guide:

User's Guide
============

Starting with the example shown in the introduction, let's dig into configclasses a bit::

    from configclasses import configclass

    # Wrap your configuration class in the `configclass` decorator
    @configclass
    class Configuration:
        HOST: str
        PORT: int

    # Fields are populated when you construct a Configuration instance
    config = Configuration()

    # Access fields by name.
    config.HOST == "localhost"

You start by defining your own configuration class with the fields that
you will need for your application. This is done exactly in the same way that
it is done with dataclasses (`PEP-557 <https://www.python.org/dev/peps/pep-0557/>`_).

.. note:: If you're not familiar with `dataclasses <https://www.python.org/dev/peps/pep-0557/>`_,
  they are a way of describing classes in python using type annotations that removes much of the 
  boilerplate. The ideas have existed for some time in alternative forms as 
  `attrs <https://github.com/python-attrs/attrs>`_,
  `recordType <https://code.activestate.com:443/recipes/576586-dot-style-nested-lookups-over-dictionary-based-dat>`_,
  `namedtuple <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_, etc. I would suggest
  familiarizing yourself with the functionality before continuing to get the most out of this guide.

The key distinction between a dataclass and a configclass is that the fields of a dataclass
are not populated from within the code itself. Instead, a configclass knows how to fetch the value
for each field from sources of configuration that `live outside the code`. 

When a dataclass is constructed, the ``__init__`` method searches for configuration variables that match 
the field names, and assigns the values to the matching configclass field. By default, that source of 
configuration is the application's environment variables. 

.. code-block:: bash

    $ HOST=localhost PORT=8000 python application.py

``Configuration`` has a field named ``HOST``, so it will search the environment for a variable
with the same name. The value of the environment variable is assigned to the ``HOST`` field.

``PORT`` is also found and assigned to the matching field. Notice that it is defined as an ``int``
type. Because of this, it is converted into an integer value before assignment. If the ``PORT`` environment
variable cannot be converted into an ``int``, an exception is raised.

Field Types
^^^^^^^^^^^

So far, we have discussed string and integer fields. But configclasses supports other types as well.
These include bools, floats, json objects, lists, key-value pairs, and custom types. It also includes
enums for when you want to limit the valid set of values for a field.

Let's see that in action::

  
    from configclasses import configclass, enums

    # Wrap your configuration class in the `configclass` decorator
    @configclass
    class Configuration:
        HOST: str
        PORT: int
        ENABLE_AUTHENTICATION: bool
        LOG_LEVEL: enums.LogLevel

    # Fields are populated when you construct a Configuration instance
    config = Configuration()

    config.ENABLE_AUTHENTICATION == True
    config.LOG_LEVEL.value == logging.DEBUG

.. code-block:: bash

    $ HOST=localhost PORT=8000 ENABLE_AUTHENTICATION=true LOG_LEVEL=DEBUG python application.py

You'll notice that the fields are converted from strings in the environment into the correct
python types. Bool values should be case insensitive "true"/"false" or 1/0 respectively.

.. note:: Later we will look at sources that provide python primitive types instead of just string types. 
    Those primitive types can be converted into strings using python's truthy value rules.

``LOG_LEVEL`` uses a convenience enum that the library provides which maps the logging constants in the
stdlib's ``logging`` module into an enum class.


.. autoclass:: configclasses.enums.LogLevel(Enum)
   :noindex:

   .. attribute:: NotSet   = logging.NOTSET   =  0
   .. attribute:: Debug    = logging.DEBUG    = 10
   .. attribute:: Info     = logging.INFO     = 20
   .. attribute:: Warning  = logging.WARNING  = 30
   .. attribute:: Error    = logging.ERROR    = 40
   .. attribute:: Critical = logging.CRITICAL = 50

Values are considered valid for enums when they are either the case-insensitive name of an enum
variant or the case-insensitive value of an enum variant. There is nothing special about the 
``LogLevel`` enum defined in the library. You can define use any subclass of ``enum.Enum`` from
the python stdlib, and the same rules will apply.


Converters
^^^^^^^^^^

Richer data types require the introducion of a couple of new concepts. The field function and
its converter argument::
    
    def field(converter=None, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None)

If you are familiar with dataclasses, the function is identical to the same function
in that module, with one key difference. That is the converter argument. A ``converter``
is any function that takes a single argument and knows how to convert it into the datatype
of the configclass field. You are probably familiar with one such function already, ``json.loads``.
``json.loads`` takes a string as an argument and produces a python object as long as the string
contains valid json.

If we have a json config file such as logging_conf.json::

    {
         "version": 1,
         "formatters": {
             "default": {
                 "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
             },
         },
         "handlers": {
             "console": {
                 "class": "logging.StreamHandler",
                 "formatter":"default"
             }
         },
         "root": {
             "handlers": ["console"],
             "level": "DEBUG",
         },
     }


We would put it to use like so::

    import json
    from configclasses import configclass, field

    # Wrap your configuration class in the `configclass` decorator
    @configclass
    class Configuration:
        LOGGING_CONF: dict = field(converter=json.loads)

    # Fields are populated when you construct a Configuration instance
    config = Configuration()

    type(config.LOGGING_CONF) == dict


.. code-block:: bash
    LOGGING_CONF="$(cat logging_conf.json)" python application.py


configclasses also provides a handful of useful converters. ``_list`` takes
comma seperated values and splits them into a list. It strips whitespace unless
values are quoted. ``"foo, bar, baz, ' quix'"`` is transformed into 
``["foo", "bar", "baz", " quix"]``

``kv_list`` takes a comma seperated list of key value pairs.
``"foo=bar, baz=' quix'"`` becomes ``{"foo": "bar", "baz": " quix"}``


Sources
^^^^^^^

So far we have glossed over exactly how fields are populated from the environment. Those
details are determined by ``Source`` classes. The default source is an ``EnvironmentSource``
and the constructor looks like this ``EnvironmentSource(namespace=None)``. With the namespace
argument, we can limit the environment variables that can populate our configclass. Suppose we
have the following environment variables::

    HOST=localhost
    PORT=8000
    MYAPP_HOST=0.0.0.0
    MYAPP_PORT=80

Let's see it in action::
 
    from configclasses import configclass
    from configclasses.sources import EnvironmentSource



Field Types
Defaults
Sources
Singleton instances
Errors
Enums
Converters
Reload
Advanced patterns:
- custom sources
- field dependent sources
- bootstrapping one configclass with values from another configclass.
- Gotcha: Some sources produce python types and some always produce strings.
- Make sure that your converter functions can handle that distinction

































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

