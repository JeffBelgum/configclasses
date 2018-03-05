.. configclasses documentation master file, created by
   sphinx-quickstart on Tue Feb 27 09:18:45 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ConfigClasses
=========================================

.. image:: https://travis-ci.org/JeffBelgum/configclasses.svg?branch=master
    :target: https://travis-ci.org/JeffBelgum/configclasses

.. image:: https://codecov.io/gh/JeffBelgum/configclasses/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/JeffBelgum/configclasses

.. image:: https://img.shields.io/pypi/v/configclasses.svg
    :target: https://pypi.python.org/pypi/configclasses

.. image:: https://img.shields.io/pypi/l/configclasses.svg
    :target: https://pypi.python.org/pypi/configclasses

.. image:: https://img.shields.io/pypi/pyversions/configclasses.svg
    :target: https://pypi.python.org/pypi/configclasses


Release v\ |version|. (:ref:`Installation <install>`)


Introduction
------------

configclasses provides a simple yet powerful way to define and fetch
configuration values for your application by extending python's dataclasses
(`PEP-557 <https://www.python.org/dev/peps/pep-0557/>`_) with additional
functionality.

Configuration values are fetched on demand from various sources,
validated, and stored in a single strongly typed configuration object.


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

    # Fields are populated when you construct a Configuration instance
    config = Configuration()

    # Access fields by name.
    config.HOST == "localhost"

That's it!

You now have a easy to use configuration class that fetches and validates all the
configuration values your application requires. It defaults to searching environment
variables to populate fields. In this case, it expects environment variables to be
set for ``HOST``, ``PORT``, and ``DATABASE``.

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
    # singleton object. This way you can create a reference to
    # it from any module you like and the configuration values
    # will be consistent from instance to instance.
    config = Configuration()

    # Access fields by name.
    config.HOST == "localhost"

The ``Configuration`` class will now search command line arguments, environment variables,
and a `.env` file for ``HOST``, ``PORT``, and ``DATABASE``.

If a field name is found in multiple sources, sources are prioritized in the order they
are passed to the ``configclass`` decorator, giving the first source the highest priority.


Features
^^^^^^^^

  * Globally accessible configuration classes
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

Tutorials to guide you through the most common uses of the library as
well as more advanced scenarios.

.. toctree::
  :maxdepth: 2

  guide

API Documentation
-----------------

Here is where you'll find comprehensive documentation for the public api.

.. toctree::
   :maxdepth: 2

   api


Contribution
------------

Contributors are the best!

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
