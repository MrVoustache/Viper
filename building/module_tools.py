from typing import Any, Optional, Callable

def replace_module(name : str, value : Any) -> None:
    """
    Replaces the module with given name by value.
    Warning : this is permanent during the lifetime of this interpreter.
    """
    if name.__class__ != str:
        raise TypeError("Name must be a str, got "+repr(name.__class__.__name__))
    import sys
    if name not in sys.modules:
        raise KeyError("Module has not been loaded (nor pre-loaded)")
    sys.modules[name] = value


def get_if_imported(module : str, value : Optional[str] = None) -> Any:
    """
    Returns the module or object in the module if it has been loaded.
    Returns None otherwise.
    """
    if module.__class__ != str or (value != None and value.__class__ != str):
        raise TypeError("Expected str, str or None, got "+repr(module.__class__.__name__)+" and "+repr(value.__class__.__name__))
    import sys
    if module in sys.modules:
        m = sys.modules[module]
        if value != None and value in dir(m):
            return dir(m)[value]
        return m

def clean_annotations(*clss : type) -> None:
    """
    Cleans the annotations of objects in a class (or classes) :
    Replaces the class name as str by the actual class.

    Example:

    class Foo:

        def new(self) -> 'Foo':
            return Foo()
    
    clean_annotations(Foo)

    print(Foo.new.__annotations__)

    >>> {'return': <class '__main__.Foo'>}

    When given multiple classes, it will also clean them globally (cleaning the appearances of each class into each other).
    """
    for cls in clss:
        if not isinstance(cls, type):
            raise TypeError("Expected class, got "+repr(cls.__class__.__name__))
    

    def clean_typing(t, name, value):
        from typing import _GenericAlias, ForwardRef
        if t == name or t == ForwardRef(name):
            t = value
        elif isinstance(t, _GenericAlias) and hasattr(t, "__args__"):
            t.__args__ = tuple(clean_typing(ti, name, value) for ti in t.__args__)
        return t
    
    work = set()
    for cls in clss:
        l = [getattr(cls, att) for att in dir(cls)]
        for obj in filter(lambda obj: not isinstance(obj, type), l):
            try:
                work.add(obj)
            except:
                pass
    work.update(clss)

    for cls in clss:

        name = cls.__name__

        for obj in filter(lambda obj: hasattr(obj, "__annotations__"), work):
            for k, ann in obj.__annotations__.items():
                obj.__annotations__[k] = clean_typing(ann, name, cls)

def buffer_function(f : Callable) -> Callable:

    _buffer = []
    _dict_buffer = {}

    def buffered_f(*args, **kwargs):
        try:
            if (args, kwargs) in _dict_buffer:
                return _dict_buffer[args, kwargs]
        except TypeError:
            for k, v in _buffer:
                if k == (args, kwargs):
                    return v
        r = f(*args, **kwargs)
        try:
            _dict_buffer[args, kwargs] = r
        except:
            _buffer.append(((args, kwargs), r))
        return r
    
    return buffered_f

del Any, Optional