"""
This module adds metaclasses that give classes a custom method resolution order in context managers.

When a class becomes a context, it is placed at the top of the MRO.
Subsequent contexts will place other classes on top of previous ones

For example:

>>> class dog(metaclass = ???):
...     def bark(self):
...         print("Wooof!")
...
>>> class husky(dog):
...     def bark(self):
...         print("AAAAAWAAAAWAAAWA!")
>>> Keith = husky()
>>> Keith.bark()
AAAAAWAAAAWAAAWA!
>>> with dog:
...     Keith.bark()
...
Wooof!
>>> with dog:
...     with husky:
...         Keith.bark()
...
AAAAAWAAAAWAAAWA!
"""