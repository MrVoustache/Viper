# Viper
A Python library full of useful Python tools.

Viper adds many missing tools and improves many existing tools in Python.
For example, this includes frozendicts, DeamonThread class, other Thread subclasses, improved ABCs, debugging tools, new decorators and classes, etc.
It is designed to feel very Python-like.

To list all of the available packages, simply Python's interactive prompt and explore:

```
>>> from Viper import *
>>> dir()
['__annotations__', '__builtins__', '__doc__', '__loader__', '__name__', '__package__', '__spec__', 'abc', 'better_threading', 'building', 'compress', 'debugging', 'exceptions', 'format', 'frozendict', 'interactive', 'meta', 'pickle_utils', 'warnings']
>>> help(better_threading)
Help on module Viper.better_threading in Viper:

NAME
    Viper.better_threading - This module adds new classes of threads, including one for deamonic threads, but also fallen threads and useful multithreading tools.

...
```
