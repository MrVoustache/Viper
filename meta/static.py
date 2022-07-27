"""
This module adds metaclasses that make a class a statically-typed class.
For such a class, all of its methods would first check if their arguments match the type annotations when called.
Note that no annotations is equivalent to Typing.Any, except for:
    - self (first argument) of normal methods will be interpreted as an instance of the class.
    - cls (first argument) of class methods will be interpreted as the class itself or one of its subclasses.
"""