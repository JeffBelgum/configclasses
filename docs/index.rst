.. configclasses documentation master file, created by
   sphinx-quickstart on Tue Feb 27 09:18:45 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ConfigClasses
=========================================

Release v\ |version|. (:ref:`Installation <install>`)


Introduction
------------

Think python's dataclasses module (`PEP-557 <https://www.python.org/dev/peps/pep-0557/>`_) for configuration.
Pulls in configuration from various sources into a single integrated, global configuration
object. The configuration data can be reloaded on demand.


A Basic Example
^^^^^^^^^^^^^^^

::

    from configclasses import configclass
    
    # Wrap your configuration class in the `configclass` decorator
    @configclass
    class Configuration:
        HOST: str
        PORT: int
        DATABASE: str
    
    # Instantiating `Configuration` will always return the same 
    # singleton object. This way you can create a reference to 
    # it from any module you like and the configuration values 
    # will be consistent from instance to instance.
    config = Configuration()
    
    # Access fields by name.
    config.HOST == "localhost"

``configclass`` defaults to searching environment variables to populate fields.
In this case, it expects environment variables to be set for ``HOST``, ``PORT``,
and ``DATABASE``.

A `Slightly` More Advanced Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``configclass`` decorator also accepts user-specified sources of configuration
data.

::
  
    from configclasses import configclass, sources

    # Create multiple sources of configuration information.
    cli_source = sources.CommandLineSource()
    env_var_source = sources.EnvironmentSource()
    dot_env_source = sources.DotEnvSource(path=".env")

    # Pass sources to the `configclass` decorator.
    @configclass(sources=[cli_source, env_var_source, dot_env_source])
    class Configuration:
        HOST: str
        PORT: int
        DATABASE: str = "psql://localhost:5432"  # Set a default value
    
    # Instantiating `Configuration` will always return the same 
    # singleton object.
    config = Configuration()
    
    # Access fields by name.
    config.HOST == "localhost"
        
The ``Configuration`` class will now search command line arguments, environment variables,
and a `.env` file for ``HOST``, ``PORT``, and ``DATABASE``. 

If a field name is found in multiple sources, sources are prioritized in the order they 
are passed to the ``configclass`` decorator, giving the first source the highest priority.


Features
^^^^^^^^

  * Globally accessable configuration classes
  * Easily pull from many sources of configuration:

    - Environment variables
    - Command line arguments
    - Dotenv files
    - Json files
    - Toml files
    - Ini files
    - Consul Key/Value store
    - Planned sources: AWS Parameter Store, Etcd, Redis

  * Specify prioritization when multiple sources are used together.
  * Support for strongly typed configuration values out of the box:

    - primitive types such as ``int``, ``float``, and ``str`` are supported.
    - ``Enum`` types can be used to specify valid values
    - ``converter`` functions can turn stringly typed values complex types 
      such as dicts or your own types.

Planned work
^^^^^^^^^^^^

  * Deal with sources that only provide stringly typed values and values that provide other primitives
  * Some sources might be case-insensitive.
  * Async/Sync versions of sources
  * Research and design push updates (as opposed to polling updates)
  * Better error messages when config values are missing from all sources
  * Audit exception types raised.
  * Comprehensive docs

    + Includes docs on adding your own sources.


Installation
------------

.. toctree::
  :maxdepth: 2

  install


User's Guide
------------

.. toctree::
  :maxdepth: 2

  guide

API Documentation
-----------------

What are the api docs about?

.. toctree::
   :maxdepth: 2

   api


Contribution
------------

.. toctree::
  :maxdepth: 2

  contribution


License
-------

Licensor solely permits licensee to license under either of the following two options
 * `MIT license <http://opensource.org/licenses/MIT>`_
 * `Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_

.. toctree::
  :maxdepth: 2

  license


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
