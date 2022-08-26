"""
This module adds a few methods and classes that make using pickle easier and more secure.
"""

from Viper.abc.io import BytesReader
from pickle import Unpickler, UnpicklingError
from typing import Any, Dict, Iterable, Iterator
from Viper.warnings import VulnerabilityWarning

__all__ = ["PickleVulnerabilityWarning", "ForbiddenPickleError", "WhiteListUnpickler", "BlackListUnpickler", "safe_load", "safe_loads"]





class PickleVulnerabilityWarning(VulnerabilityWarning):

    """
    This warning indicates that pickle is being used in an insecure way: a vulnerability could be used to trigger arbitrary code execution!
    Look into the module where the present warning class is defined (Viper.pickle_utils) to find resources to help secure your code.
    """




class ForbiddenPickleError(UnpicklingError):

    """
    This exception indicates that an unpickling operation was attempted on a pickle that is forbidden in the present context.
    """




class WhiteListUnpickler(Unpickler):
    
    """
    This subclass of unpickler can only load object that have already been registered to their whitelist.
    """

    def __init__(self, file: BytesReader, *, fix_imports: bool = True, encoding: str = 'ASCII', errors: str = 'strict', buffers: Iterable[Any] | None = None) -> None:
        super().__init__(file, fix_imports = fix_imports, encoding = encoding, errors = errors, buffers = buffers)
        from typing import Any
        self._wlist : Dict[tuple[str, str], Any] = {}

    def allow(self, *objects : Any):
        """
        Allows one or multiple classes, functions, methods, etc. to be loaded by this instance of WhiteListUnpickler. 
        """
        from inspect import getmodule
        added = {}
        for object in objects:
            mod = getmodule(object)
            if mod == None:
                raise ValueError("Object {} cannot be mapped to any containing module.".format(repr(object)))
            obj_name = None
            for name in dir(mod):
                if getattr(mod, name) is object:
                    obj_name = name
                    break
            if obj_name == None:
                raise ValueError("Cannot find the name of object {} in module '{}'.".format(repr(object), mod.__name__))
            added[(mod.__name__, obj_name)] = object
        self._wlist.update(added)
    
    def forbid(self, *objects : Any):
        """
        Forbids one or multiple classes, functions, methods, etc. to be loaded by this instance of WhiteListUnpickler. 
        """
        from inspect import getmodule
        removed = {}
        for object in objects:
            mod = getmodule(object)
            if mod == None:
                raise ValueError("Object {} cannot be mapped to any containing module.".format(repr(object)))
            obj_name = None
            for name in dir(mod):
                if getattr(mod, name) is object:
                    obj_name = name
                    break
            if obj_name == None:
                raise ValueError("Cannot find the name of object {} in module '{}'.".format(repr(object), mod.__name__))
            removed[(mod.__name__, obj_name)] = object
        for entry, object in removed.items():
            if entry not in self._wlist or self._wlist[entry] is not object:
                raise KeyError("Object was already not allowed.")
        for entry, object in removed.items():
            self._wlist.pop(entry)
    
    def allowed(self) -> Iterator[Any]:
        """
        Iterates over all of the allowed objects.
        """
        return self._wlist.values()

    def find_class(self, __module_name: str, __global_name: str) -> Any:
        if (__module_name, __global_name) not in self._wlist:
            raise ForbiddenPickleError("Cannot import object '{}' from module '{}' as it is not on the unpickler's whitelist.".format(__global_name, __module_name))
        obj = super().find_class(__module_name, __global_name)
        if obj != self._wlist[(__module_name, __global_name)]:
            raise ForbiddenPickleError("Cannot import object '{}' from module '{}' as it is not on the unpickler's whitelist.".format(__global_name, __module_name))
        return obj




class BlackListUnpickler(Unpickler):

    """
    This subclass of unpickler can only load object that have not already been registered to their blacklist.
    """

    def __init__(self, file: BytesReader, *, fix_imports: bool = True, encoding: str = 'ASCII', errors: str = 'strict', buffers: Iterable[Any] | None = None) -> None:
        super().__init__(file, fix_imports = fix_imports, encoding = encoding, errors = errors, buffers = buffers)
        from typing import Any
        self._blist : Dict[tuple[str, str], Any] = {}

    def forbid(self, *objects : Any):
        """
        Forbids one or multiple classes, functions, methods, etc. to be loaded by this instance of WhiteListUnpickler. 
        """
        from inspect import getmodule
        added = {}
        for object in objects:
            mod = getmodule(object)
            if mod == None:
                raise ValueError("Object {} cannot be mapped to any containing module.".format(repr(object)))
            obj_name = None
            for name in dir(mod):
                if getattr(mod, name) is object:
                    obj_name = name
                    break
            if obj_name == None:
                raise ValueError("Cannot find the name of object {} in module '{}'.".format(repr(object), mod.__name__))
            added[(mod.__name__, obj_name)] = object
        self._blist.update(added)
    
    def allow(self, *objects : Any):
        """
        Allows one or multiple classes, functions, methods, etc. to be loaded by this instance of WhiteListUnpickler. 
        """
        from inspect import getmodule
        removed = {}
        for object in objects:
            mod = getmodule(object)
            if mod == None:
                raise ValueError("Object {} cannot be mapped to any containing module.".format(repr(object)))
            obj_name = None
            for name in dir(mod):
                if getattr(mod, name) is object:
                    obj_name = name
                    break
            if obj_name == None:
                raise ValueError("Cannot find the name of object {} in module '{}'.".format(repr(object), mod.__name__))
            removed[(mod.__name__, obj_name)] = object
        for entry, object in removed.items():
            if entry not in self._blist or self._blist[entry] is not object:
                raise KeyError("Object was already not allowed.")
        for entry, object in removed.items():
            self._blist.pop(entry)
    
    def forbidden(self) -> Iterator[Any]:
        """
        Iterates over all of the forbidden objects.
        """
        return self._blist.values()

    def find_class(self, __module_name: str, __global_name: str) -> Any:
        if (__module_name, __global_name) in self._blist:
            raise ForbiddenPickleError("Cannot import object '{}' from module '{}' as it is on the unpickler's blacklist.".format(__global_name, __module_name))
        obj = super().find_class(__module_name, __global_name)
        if obj == self._blist[(__module_name, __global_name)]:
            raise ForbiddenPickleError("Cannot import object '{}' from module '{}' as it is on the unpickler's blacklist.".format(__global_name, __module_name))
        return obj





def safe_loads(data : bytes | bytearray | memoryview) -> Any:
    """
    Loads given pickle using only safe builtins.
    """
    if not isinstance(data, bytes | bytearray | memoryview):
        raise TypeError("Expected readable buffer, got " + repr(type(data).__name__))
    import builtins
    import _sitebuiltins
    from io import BytesIO
    safe_builtins = [obj for obj in map(lambda x : getattr(builtins, x), dir(builtins)) if isinstance(obj, type)] + [abs, aiter, all, any, anext, ascii, bin, breakpoint, callable, chr, compile, delattr, dir, divmod, format, getattr, globals, hasattr, hash, _sitebuiltins._Helper, hex, id, input, isinstance, issubclass, iter, len, locals, max, min, next, oct, open, ord, pow, print, repr, round, setattr, sorted, sum, vars]
    unpickler = WhiteListUnpickler(BytesIO(data))
    unpickler.allow(*safe_builtins)
    return unpickler.load()

def safe_load(file : BytesReader) -> Any:
    """
    Loads pickle from given file using only safe builtins.
    """
    from Viper.abc.io import BytesReader
    if not isinstance(file, BytesReader):
        raise TypeError("Expected readable byte-stream, got " + repr(type(file).__name__))
    import builtins
    import _sitebuiltins
    safe_builtins = [obj for obj in map(lambda x : getattr(builtins, x), dir(builtins)) if isinstance(obj, type)] + [abs, aiter, all, any, anext, ascii, bin, breakpoint, callable, chr, compile, delattr, dir, divmod, format, getattr, globals, hasattr, hash, _sitebuiltins._Helper, hex, id, input, isinstance, issubclass, iter, len, locals, max, min, next, oct, open, ord, pow, print, repr, round, setattr, sorted, sum, vars]
    unpickler = WhiteListUnpickler(file)
    unpickler.allow(*safe_builtins)
    return unpickler.load()



del BytesReader, Unpickler, UnpicklingError, Any, Dict, Iterable, Iterator, VulnerabilityWarning