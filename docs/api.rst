.. _api:

API Documentation
=================

.. module:: configclasses

The API documentation covers the full public api for the library including
examples for more complicated features. The configclass decorator is described
followed by pluggable sources of configuration values, and finally convenience
enums and data type conversion functionality.

Configclass
-----------

.. autofunction:: configclass(source: Source=None, sources: List[Source]=None)

.. autofunction:: field(converter=None, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None)


Sources
-------

.. automodule:: configclasses.sources

.. autoclass:: configclasses.sources.EnvironmentSource(namespace=None, environ=os.environ)
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.DotEnvSource
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.CommandLineSource(argparse=None, argv=sys.argv)
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.JsonSource
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.TomlSource
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.IniSource
   :members:
   :inherited-members:

.. autoclass:: configclasses.sources.ConsulSource(root, namespace="", http=requests)
   :members:
   :inherited-members:



Enums
-----
.. automodule:: configclasses.enums

.. autoclass:: configclasses.enums.LogLevel(Enum)

   .. attribute:: NotSet = logging.NOTSET
   .. attribute:: Debug = logging.DEBUG
   .. attribute:: Info = logging.INFO
   .. attribute:: Warning = logging.WARNING
   .. attribute:: Error = logging.ERROR
   .. attribute:: Critical = logging.CRITICAL

.. autoclass:: configclasses.enums.Environment(Enum)

   .. attribute:: Development = 0
   .. attribute:: Test = 1
   .. attribute:: Staging = 2
   .. attribute:: Production = 3


Conversions
-----------

Conversion functions that can be specified as the ``converter`` in a configclass field.

.. autofunction:: configclasses.conversions.csv_list

.. autofunction:: configclasses.conversions.csv_pairs
