"""
configclasses provides a simple yet powerful way to define and fetch
configuration values for your application by extending python's dataclasses
with additional functionality.

See full documentation at <https://configclasses.readthedocs.io/en/latest/>

:copyright: (c) 2018 by Jeff Belgum.
:license: MIT or Apache 2.0, see LICENSE-MIT and LICENSE-APACHE for more details.
"""

__version__ = "0.4.3"


from . import conversions, enums, sources
from .configclass import configclass, field
