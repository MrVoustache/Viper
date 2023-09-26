# Viper
A Python library full of useful Python tools.

Viper adds many missing tools and improves many existing tools in Python.
For example, this includes frozendicts, a more advanced IO interface, improved ABCs, debugging tools, new decorators, types of classes, even new types of modules, etc.
It is designed to feel very Python-like.

To list all of the available packages, simply Python's interactive prompt and explore:

```
>>> from Viper import *
>>> import Viper
>>> dir(Viper)
['__all__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__path__', '__spec__', 'abc', 'debugging', 'exceptions', 'format', 'frozendict', 'interactive', 'io', 'meta', 'pickle_utils', 'warnings']
>>> help(io)
Help on module Viper.io in Viper:

NAME
    Viper.io - This module adds some useful IO tools. This includes IO buffer and pipe/circular buffers for both bytes and strings.

CLASSES
    Viper.abc.io.BytesIO(Viper.abc.io.BytesReader, Viper.abc.io.BytesWriter, Viper.abc.io.IO)
        BytesBuffer
        BytesIO
    Viper.abc.io.StringIO(Viper.abc.io.StringReader, Viper.abc.io.StringWriter, Viper.abc.io.IO)
        StringBuffer
        StringIO

    class BytesBuffer(Viper.abc.io.BytesIO)
...
```

Some practical and classical examples of the content of Viper include:
- Making iterable classes:
```
>>> class MyClass(metaclass = Viper.meta.iterable.InstanceReferencingClass):
...     pass
... 
>>> c = MyClass()
>>> list(MyClass)[0] is c
True
>>> del c
>>> len(list(MyClass))
0
```
This is useful for classes for which you want to keep track of the instances or for which you need to perform some operations on.

- Timing function calls and generate performance reports:
```
>>> c = Viper.debugging.chrono.Chrono()
>>> @c
... def fibo(n):
...     if n <= 0:
...         return 0
...     if n == 1:
...         return 1
...     return fibo(n - 1) + fibo(n - 2)
...
>>> fibo(25)
75025
>>> Viper.debugging.chrono.print_report(c)
Execution report featuring 1 functions or methods, over 375ms.
Per function results :
Function __main__.fibo
        Calls : 242785, Total :   375ms   , Average : 1µs, 545ns, Proportion : 100.0% of the time
```
You can use one Chrono object on multiple functions. It becomes useful if you need to know what part of your code you should optimize first.

- Flux operators:
```
>>> buffer = Viper.io.BytesIO()
>>> buffer << Viper.pickle_utils.StreamPickler("This is a test object")
>>> buffer.seek(0)
0
>>> Viper.pickle_utils.StreamUnpickler() << buffer
'This is a test object'
```
Flux operator define a much stronger, safer and handy interface than Python IOs. Furthermore, this syntax is revertible and stackable for constants:
```
>>> buffer = Viper.io.StringIO()
>>> "Good!\n" >> (buffer << "Hello!\n" << "How are you doing?\n")
<Viper.io.StringIO object at 0x000002A2F862E4A0>
>>> buffer.seek(0)
0
>>> buffer.readable
Budget(32)
>>> print(buffer.read(buffer.readable.value))
Hello!
How are you doing?
Good!
```
- And many other useful random features!

Note that this library is extensively documented. Use Python's help system (for example the help function while in an interactive interpreter) to learn how to use all the modules and classes.