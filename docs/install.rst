.. _install:

Installation
============

``configclasses`` can be installed with all the traditional python tools.


Virtual Environment
-------------------
It is best practice to install packages into an isolated python environment.
The most common method is to create and activate a virtual environment with
virtualenv::

    $ virtualenv venv
    $ source venv/bin/activate

If you don't have `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ installed,
follow the instructuions in their documentation.


Pip Install configclasses
-------------------------

To install configclasses, simply run this command in your terminal::

    $ pip install configclasses

If you don't have `pip <https://pip.pypa.io>`_ installed,
`this Python installation guide <http://docs.python-guide.org/en/latest/starting/installation/>`_
can guide you through the process.


Suggested Alternative: Pipenv
-------------------------------

`pipenv <https://github.com/pypa/pipenv>`_ is a new tool that solves the problems of
isolated virtual environment, package installation, and dependency tracking in a
simple but comprehensive manner::

    $ pip install pipenv
    $ pipenv install configclasses

Full documentation can be found on `readthedocs <https://pipenv.readthedocs.io/en/latest/>`_
Give it a try!


Get the Source Code
-------------------

configclasses is under active development on GitHub, where the code is
`always available <https://github.com/jeffbelgum/configclasses>`_.

You can clone the repository::

    $ git clone git://github.com/jeffbelgum/configclasses.git

Once you have a copy of the source, you can embed it in your own Python
packae or install it into your site-packages easily::

    $ python setup.py install


