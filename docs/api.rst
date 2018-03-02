.. _api:

Application Developer Interface
===============================


.. module:: configclasses


Main
----

.. decorator:: configclass

   Turn a class into a configclass with the default EnvironmentSource used.

For example, configuring the host and port for a web application might look
like this::

  from configclasses import configclass

  @configclass
  class Configuration:
      HOST: str
      PORT: int

.. decorator:: configclass(source: Source = None, sources: List[Source] = None)

   Turn a class into a configclass using the user provided source or sources list.

   The user must pass `either` the source `or` a list of sources. Providing both
   is an error and will raise a ``ValueError``.

Configuring the host and port for a web application using both command line arguments
and environment variables as sources::

  from configclasses import configclass, sources

  cli_source = CommandLineSource()
  env_source = EnvironmentSource()
  @configclass(sources=[cli_source, env_source])
  class Configuration:
      HOST: str
      PORT: int

Because the ``cli_source`` comes before the ``env_source`` in the list of ``sources``,
it will be prioritized when choosing values that are found in both sources.

.. function:: field(converter=None, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None)

   Return an object to identify configclass fields.

   converter is a function that takes a single argument and constructs
   a return value that is the same as the conficlass field's type annotation.
   default is the default value of the field.
   default_factory is a 0-argument function called to initialize a field's value.
   If init is True, the field will be a parameter to the class's __init__() function.
   If repr is True, the field will be included in the object's repr().
   If hash is True, the field will be included in the object's hash().
   If compare is True, the field will be used in comparison functions.
   metadata, if specified, must be a mapping which is stored but not otherwise
   examined by dataclass.

   It is an error to specify both default and default_factory.

This function can be used if the field differs from the default functionality.
It is the same as the field function in the dataclasses module except that it
includes a ``converter`` argument that can be used to convert from a primitive
type to a more complex type such as a dict or custom class.


Sources
-------
..  autoclass:: EnvironmentSource
.. autoclass:: DotEnvSource
..  autoclass:: CommandLineSource
.. autoclass:: JsonSource
.. autoclass:: TomlSource
.. autoclass:: IniSource
.. autoclass:: ConsulSource



Enums
-----

.. autoclass:: LogLevel
   :members:
   :undoc-members:

.. class:: LogLevel(Enum)

   ``NotSet = NOTSET``

   Debug = DEBUG

   Info = INFO

   Warning = WARNING

   Error = ERROR

   Critical = CRITICAL

Python logging module log level constants represented as an ``enum.Enum``.


.. autoclass:: Environment
   :members:
   :undoc-members:

.. class:: Environment(Enum)

   Development = 0

   Test = 1

   Staging = 2

   Production = 3

Convenience enum provides common environment names.


Conversions
-----------
.. function:: kv_list(value: str) -> dict

   kv lists are comma seperated pairs of values where a pair is defined as
   `key=value`. Whitespace around a key or value is stripped unless text is quoted.

   Skips empty pairs and raises an exception on any other malformed pair

For example::

   kv_list("a=1,b=2")
   # {"a": 1, "b": 2}
