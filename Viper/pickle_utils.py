"""
This module adds a few methods and classes that make using pickle easier and more secure.
"""

import pickle
from functools import wraps
from pickle import Pickler, Unpickler, UnpicklingError
from pickle import load as _old_load
from pickle import loads as _old_loads
from threading import RLock
from typing import Any

from .abc.io import BytesReader, BytesWriter
from .io import BytesBuffer, BUFFER_SIZE
from .warnings import VulnerabilityWarning

__all__ = ["PickleVulnerabilityWarning", "ForbiddenPickleError", "StreamUnpickler", "StreamPickler", "RestrictiveUnpickler", "SafeBuiltinsUnpickler", "WhiteListUnpickler", "BlackListUnpickler", "safe_load", "safe_loads"]





class PickleVulnerabilityWarning(VulnerabilityWarning):

    """
    This warning indicates that pickle is being used in an insecure way: a vulnerability could be used to trigger arbitrary code execution!
    Look into the module where the present warning class is defined (Viper.pickle_utils) to find resources to help secure your code.
    """





class ForbiddenPickleError(UnpicklingError):

    """
    This exception indicates that an unpickling operation was attempted on a pickle that is forbidden in the present context.
    """





@wraps(_old_load)
def load(*args, **kwargs) -> Any:
    from warnings import warn
    warn(PickleVulnerabilityWarning("Using pickle.load without further protection."))
    try:
        return _old_load(*args, **kwargs)
    except BaseException as e:
        raise e

pickle.load = load


@wraps(_old_loads)
def loads(*args, **kwargs) -> Any:
    from warnings import warn
    warn(PickleVulnerabilityWarning("Using pickle.loads without further protection."))
    try:
        return _old_loads(*args, **kwargs)
    except BaseException as e:
        raise e

pickle.loads = loads





class StreamUnpickler(Unpickler, BytesWriter):

    """
    A subclass of Unpickler that can be written to like a file. You can write to it until the pickle object has been reconstructed.
    Note that the unpickling process is done in background : data written to this stream will be immediately used.
    """

    class __ReaderRegulatedBuffer(BytesBuffer):

        """
        A subclass of bytes buffer that constrains writable space by what is expected to be read in the other end.
        The writable property will block until it has received a value. Zero indicates the end.
        """

        def __init__(self, size: int = BUFFER_SIZE) -> None:
            super().__init__(size)
            self.writable.value = 0

        def read(self, size: int) -> bytes:
            with self.read_lock:
                self.writable.value += size
                result = super().read(size)
                return result
            
        def readline(self, size: int | None = None) -> bytes:
            raise NotImplementedError("'readline' is not supported yet by StreamUnpicklers")
            if size is None:    # We have to read an entire line, no matter how long it is.
                line = bytearray()
                from .abc.io import STREAM_PACKET_SIZE
                with self.read_lock:
                    while True:
                        self.writable.value += STREAM_PACKET_SIZE
                        result = super().readline(STREAM_PACKET_SIZE)
                        line.extend(result)
                        if result.endswith(b"\n"):
                            self.writable.value = 0
                            return bytes(line)
            else:
                with self.read_lock:
                    self.writable.value += size
                    result = super().readline(size)
                    return result

        def readinto(self, buffer: bytearray | memoryview) -> int:
            with self.read_lock:
                self.writable.value += len(buffer)
                result = super().readinto(buffer)
                return result
        
        def write(self, data: bytes | bytearray | memoryview) -> int:
            with self.writable:
                result = super().write(data)
                self.writable.value = max(0, self.writable.value - result)
                return result



    from .abc.io import IOClosedError as __IOClosedError, IOReader as __IOReader

    __slots__ = {
        "__buffer" : "The internal buffer storing data to unpickle.",
        "__object" : "A placeholder for the unpickled object.",
        "__ready" : "An event that is set when the unpickling process finishes (or crashes).",
        "__exception" : "An eventual exception that occured in the unpickling thread.",
        "__load_lock" : "A lock on the internal load function to avoid loading the same data simultenously."
    }

    def __init__(self) -> None:
        from threading import Event, Lock, Thread
        from pickle import Unpickler
        from .abc.io import BytesWriter
        self.__buffer = self.__ReaderRegulatedBuffer()
        self.__object = None
        self.__ready = Event()
        self.__exception = None
        self.__load_lock = Lock()
        Unpickler.__init__(self, self.__buffer, fix_imports=True, encoding="ASCII", errors="strict", buffers=None)      # Let's not care about Python 2
        BytesWriter.__init__(self)
        with self.__load_lock:
            Thread(target=self.__load, daemon=True, name="StreamUnpickler reconstructor thread").start()

    def __load(self):
        """
        Internal function used to reconstruct the object.
        """
        with self.__load_lock:
            if self.closed:
                raise self.__IOClosedError("Object has already been loaded")
            if self.__ready.is_set():
                return self.__object
            try:
                self.__object = super().load()
            except BaseException as e:
                self.__exception = e
            self.__ready.set()
            self.close()

    @property
    def lock(self) -> RLock:
        return self.__buffer.write_lock
    
    @property
    def writable(self):
        return self.__buffer.writable
    
    @property
    def write_lock(self) -> RLock:
        return self.__buffer.write_lock
    
    def fileno(self) -> int:
        raise OSError(f"{type(self).__name__} objects have no associated file descriptors")
    
    def close(self):
        self.__buffer.close()

    @property
    def closed(self) -> bool:
        return self.__buffer.closed
    
    def tell(self) -> int:
        return self.__buffer.tell()
    
    def seekable(self) -> bool:
        return False
    
    def truncate(self, size: int | None = None):
        raise OSError(f"{type(self).__name__} is not truncable")
    
    def write(self, data: bytes | bytearray | memoryview) -> int:
        return self.__buffer.write(data)
    
    def load(self) -> Any:
        """
        Loads the object from data written to the stream.
        The task is actually done in background. This method just waits for the task to complete and returns the reconstructed object.
        """
        self.__ready.wait()
        if self.__exception:
            raise self.__exception
        return self.__object
    
    def __lshift__(self, other):
        if isinstance(other, self.__IOReader):
            super().__lshift__(other)
            return self.load()
        else:
            return super().__lshift__(other)
        


    

class StreamPickler(Pickler, BytesReader):

    """
    A subclass of Pickler that can be read from like a file. You can read from it until the object has been entirely pickled.
    Note that the pickling process is done in background : data can be read immediately from this stream.
    """        

    from .abc.io import IOClosedError as __IOClosedError, IOReader as __IOReader

    __slots__ = {
        "__buffer" : "The internal buffer storing the pickled data.",
        "__object" : "A placeholder for the object to pickle.",
        "__ready" : "An event that is set when the pickling process can start.",
        "__dump_lock" : "A lock that ensures exclusivity of the pickler process.",
        "__dump_method_lock" : "A lock that ensures that setting the object to pickle is a one-time operation.",
        "__started" : "An event that is set when the pickling thread has started.",
        "__finished" : "An event that is set when the pickling thread finished (or crashes).",
        "__exception" : "An eventual exception that occured in the unpickling thread.",
    }

    def __init__(self, *args) -> None:
        from threading import Event, Lock, Thread
        from .io import BytesBuffer
        from pickle import Pickler
        from .abc.io import BytesReader
        if len(args) > 1:
            raise ValueError("Expected at most one argument : the object to pickle")
        self.__buffer = BytesBuffer()
        self.__object = None
        self.__ready = Event()
        self.__dump_lock = Lock()
        self.__dump_method_lock = Lock()
        self.__started = Event()
        self.__finished = Event()
        self.__exception : None | BaseException = None
        Pickler.__init__(self, self.__buffer, fix_imports=True)
        BytesReader.__init__(self)
        with self.__dump_lock:
            Thread(target=self.__dump, daemon=True, name="StreamPickler deconstructor thread").start()
            if args:
                self.__object = args[0]
                self.__ready.set()
        self.__started.wait()

    def __dump(self):
        """
        Internal function that will dump the given object into the stream.
        """
        with self.__dump_lock:
            if self.closed:
                from .abc.io import IOClosedError
                raise IOClosedError("Object has already been pickled")
            self.__started.set()
            self.__ready.wait()
            try:
                super().dump(self.__object)
            except BaseException as e:
                self.__exception = e
            self.close()
            self.__finished.set()

    @property
    def lock(self) -> RLock:
        return self.__buffer.read_lock
    
    @property
    def readable(self):
        if self.closed:
            with self.__dump_lock:
                if self.__exception:
                    exc, self.__exception = self.__exception, None
                    raise exc
        return self.__buffer.readable
    
    @property
    def read_lock(self) -> RLock:
        return self.__buffer.read_lock
    
    def fileno(self) -> int:
        raise OSError(f"{type(self).__name__} objects have no associated file descriptors")
    
    def close(self):
        self.__buffer.close()

    @property
    def closed(self) -> bool:
        return self.__buffer.closed
    
    def tell(self) -> int:
        return self.__buffer.tell()
    
    def seekable(self) -> bool:
        return False
    
    def read(self, size: int | float = float("inf")) -> bytes | bytearray | memoryview:
        try:
            return self.__buffer.read(size)
        finally:
            with self.__dump_lock:
                if self.__exception:
                    exc, self.__exception = self.__exception, None
                    raise exc
    
    def readinto(self, buffer: bytearray | memoryview) -> int:
        try:
            return self.__buffer.readinto(buffer)
        finally:
            with self.__dump_lock:
                if self.__exception:
                    exc, self.__exception = self.__exception, None
                    raise exc
    
    def readline(self, size: int | float = float("inf")) -> bytes | bytearray | memoryview:
        try:
            return self.__buffer.readline(size)
        finally:
            with self.__dump_lock:
                if self.__exception:
                    exc, self.__exception = self.__exception, None
                    raise exc
    
    def dump(self, obj: Any) -> None:
        """
        Dumps the object into the stream. Waits for it to be completely dumped.
        """
        with self.__dump_method_lock:
            if self.closed:
                from .abc.io import IOClosedError
                raise IOClosedError("Object has already been pickled")
            if self.__ready.is_set():
                raise RuntimeError("Pickler is already pickling an object")
            self.__object = obj
            self.__ready.set()
            self.__finished.wait()
        with self.__dump_lock:
            if self.__exception:
                exc, self.__exception = self.__exception, None
                raise exc
        
    



class RestrictiveUnpickler(StreamUnpickler):
    
    """
    This subclass of unpickler can only load object that have already been allowed.

    The permission system lets you allow:
     - single objects based on identity (using id, useful for function such as exec, print, etc.) using 'allow_object(obj)'.
     - classes and their direct instances using 'allow_class(cls)'.
     - class trees and their instances using 'allow_class_hierarchy(cls)'.
    
    You can also forbid classes directly or class trees and parts of a class tree can be allowed while others are forbidden.
    For example, given the following class structure:
    ```
    A
    └───B
        ├───C
        └───D
            └───E
                └───F
                    └───G
    ```
    The following script:
    >>> unp = RestrictiveUnpickler()
    >>> unp.allow_class_hierarchy(A)
    >>> unp.forbid_class_hierarchy(D)
    >>> unp.allow_class_hierarchy(F)

    would allow the classes A, B, C, F, G and all of their direct instances. (With each consecutive line the sets of allowed classes are : {}, {A, B, C, D, E, F, G}, {A, B, C}, {A, B, C, F, G}.)

    You can also forbid a class and allow their hierarchy.
    For example, with the previous class structure:
    >>> unp = RestrictiveUnpickler()
    >>> unp.allow_class_hierarchy(A)
    >>> unp.forbid_class(A)

    would allow all direct or indirect subclasses of A (and their instances) but not A itself (nor its instances).

    Note that when a class inherits from multiple bases, and is not allowed itself, all of its bases must be allowed (directly or not).
    Also note that you cannot forbid certain builtins classes, such as bytes, str, int, etc. They will be allowed by default but not their successors.
    """

    def __init__(self) -> None:
        super().__init__()
        from typing import Any
        self.__object_whitelist : dict[int, Any] = {}
        self.__class_whitelist : set[type] = set(self.base_classes)
        self.__class_blacklist : set[type] = set()
        self.__hierarchy_whitelist : set[type] = set()
        self.__hierarchy_blacklist : set[type] = set()
        self.allow(*self.base_classes)
    
    @property
    def base_classes(self):
        """
        This is a tuple of classes which direct instances are unchangeably allowed by pickle.
        """
        return (type(None), bool, int, float, str, bytes, tuple, list, set, frozenset, dict)

    def allow_object(self, object : Any):
        """
        Tries to allow an object for through this unpickler.
        The object must belong to a module (must match a module using inspect.getmodule(object)) and be present in the module.
        Note that testing is done with builtin function id(), thus allowing 'list(range(10))' would not necessarly work.
        """
        self.__object_whitelist[id(object)] = object

    def allow_class(self, cls : type):
        """
        Allows a class and its direct instances through this unpickler.
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected class, got '{type(cls).__name__}'")
        self.__class_whitelist.add(cls)
        self.__class_blacklist.discard(cls)
    
    def allow_class_hierarchy(self, cls : type):
        """
        Allows a class, its subclasses and its instances through this unpickler.
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected class, got '{type(cls).__name__}'")
        self.__hierarchy_whitelist.add(cls)
        self.__hierarchy_blacklist.discard(cls)

    def allow(self, *objects_or_classes : Any, hierarchical : bool = False):
        """
        Allows objects through this unpickler. If a given object is a class, its instances will also be allowed.
        If hierarchical is True, any allowed class will see its subclass tree also allowed.
        """
        if not isinstance(hierarchical, bool):
            raise TypeError(f"Expected bool for hierarchical, got '{type(hierarchical)}'")
        for obj in objects_or_classes:
            if isinstance(obj, type):
                if hierarchical:
                    self.allow_class_hierarchy(obj)
                else:
                    self.allow_class(obj)
            else:
                self.allow_object(obj)

    def forbid_object(self, object : Any):
        """
        Forbids an object if it was allowed through this unpickler.
        """
        if id(object) in self.__object_whitelist:
            self.__object_whitelist.pop(id(object))
    
    def forbid_class(self, cls : type):
        """
        Forbids a class and its direct instances through this unpickler if they were allowed.
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected class, got '{type(cls).__name__}'")
        if cls in self.base_classes:
            raise ValueError(f"Cannot forbid builtin class '{cls.__name__}'")
        self.__class_blacklist.add(cls)
        self.__class_whitelist.discard(cls)
    
    def forbid_class_hierarchy(self, cls : type):
        """
        Forbids a class, its subclasses and its instances through this unpickler if they were allowed.
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected class, got '{type(cls).__name__}'")
        self.__hierarchy_blacklist.add(cls)
        self.__hierarchy_whitelist.discard(cls)

    def is_allowed(self, obj : Any) -> bool:
        """
        Returns True if the object would be allowed by this unpickler.
        If the object is a class, its instances might also be allowed. Use 'is_class_allowed' to check if its instances would also be allowed.
        """
        if id(obj) in self.__object_whitelist:
            return True
        if isinstance(obj, type):
            return self.is_class_allowed(obj)
        return False
    
    def is_class_allowed(self, cls : type) -> bool:
        """
        Returns True if the class (and its instances) would be allowed by this unpickler.
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected a class, got '{type(cls).__name__}'")
        if cls in self.__class_whitelist:
            return True
        if cls in self.__class_blacklist:
            return False
        
        def track_class(cls : type) -> bool:
            """
            Internal function that tells whether a class is allowed thanks to its base classes.
            """
            if cls in self.__hierarchy_whitelist:
                return True
            if cls in self.__hierarchy_blacklist:
                return False
            if not cls.__bases__:
                return False    # By default, it is not allowed.
            return all(track_class(b) for b in cls.__bases__)

        return track_class(cls)
    
    def warrants(self, cls : type) -> list[type]:
        """
        Given a class, returns the list of classes that either allow or forbid this class (depending on if the class itself is allowed or forbidden).
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected a class, got '{type(cls).__name__}'")
        if cls in self.__class_whitelist or cls in self.__class_blacklist:
            return [cls]
        
        allowed = self.is_class_allowed(cls)
        
        def track_class(cls : type) -> list[type]:
            """
            Internal function returns the warrants classes of a class.
            """
            if cls in self.__hierarchy_whitelist and allowed:
                return [cls]
            if cls in self.__hierarchy_blacklist and not allowed:
                return [cls]
            if not cls.__bases__:
                return []       # By default, it has no warrants.
            w = []
            for b in cls.__bases__:
                w.extend(track_class(b))
            return w

        return track_class(cls)


    @property
    def allowed_objects(self):
        """
        The set of allowed special objects.
        """
        return self.__object_whitelist.values()
    
    @property
    def allowed_classes(self):
        """
        The set of allowed classes that currently exist in the interpreter.
        Note that is a class is allowed by 'allow_class_hierarchy', some of its subclasses might not have been imported, and thus will not be listed here while still being allowed.
        """
        s : set[type] = set()
        to_add : set[type] = self.__hierarchy_whitelist
        while to_add:
            new : set[type] = set()
            for cls in to_add:
                s.add(cls)
                new.update(cls.__subclasses__())
            to_add = new - s
        s.update(self.__class_whitelist)
        return s

    def find_class(self, __module_name: str, __global_name: str) -> Any:
        obj = super().find_class(__module_name, __global_name)
        if not self.is_allowed(obj):
            if not isinstance(obj, type):
                cls = type(obj)
            else:
                cls = obj
            warrants = [c.__name__   for c in self.warrants(cls)]
            if not warrants:
                raise ForbiddenPickleError(f"'{obj}' is not allowed in the context of this {type(self).__name__} because it has no warrant classes and the object itself was not allowed")
            else:
                if len(warrants) == 1:
                    text = f"because the class {warrants[0]} is not allowed"
                else:
                    text = "because the classes " + ", ".join(warrants[:-1]) + " and " + warrants[-1] + " are not allowed"
                raise ForbiddenPickleError(f"'{obj}' is not allowed in the context of this {type(self).__name__} {text}")
        return obj





class SafeBuiltinsUnpickler(RestrictiveUnpickler):

    """
    This class of unpickler is only able to load safe objects from the builtins module by default.
    Other objects can still be allowed in instances using the methods of the RestrictiveUnpickler class.
    """

    def __init__(self) -> None:
        super().__init__()
        import builtins
        safe_builtins = {name : getattr(builtins, name) for name in dir(builtins)}
        forbidden_builtins = {
            "eval",
            "exec",
        }
        safe_builtins = {name : value for name, value in safe_builtins.items() if name not in forbidden_builtins}
        self.allow(*safe_builtins.values())





class WhiteListUnpickler(RestrictiveUnpickler):

    """
    This is the same as a RestrictiveUnpickler.
    """





class BlackListUnpickler(RestrictiveUnpickler):
    
    """
    This is a RestrictiveUnpickler which has the 'object' class allowed by default with all of its hierarchy.
    This means that all classes are allowed by default.
    """

    def __init__(self) -> None:
        super().__init__()
        self.allow_class_hierarchy(object)





def safe_loads(data : bytes | bytearray | memoryview):
    """
    Loads given pickle using only safe builtins.
    """
    if not isinstance(data, bytes | bytearray | memoryview):
        raise TypeError("Expected readable buffer, got " + repr(type(data).__name__))

    unpickler = SafeBuiltinsUnpickler()
    unpickler << data
    return unpickler.load()


def safe_load(file : BytesReader):
    """
    Loads pickle from given file using only safe builtins.
    """
    from Viper.abc.io import BytesReader
    if not isinstance(file, BytesReader):
        raise TypeError("Expected readable byte-stream, got " + repr(type(file).__name__))
    
    unpickler = SafeBuiltinsUnpickler()
    return unpickler << file





del pickle, wraps, Pickler, Unpickler, UnpicklingError, RLock, Any, BytesReader, BytesWriter, BytesBuffer, BUFFER_SIZE, VulnerabilityWarning