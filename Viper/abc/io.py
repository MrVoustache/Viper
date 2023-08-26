"""
This module stores multiple simpler interfaces for stream manipulation.
"""

from abc import ABCMeta, abstractmethod
from io import SEEK_CUR, SEEK_END, SEEK_SET
from threading import Lock, RLock
from typing import Generic, Iterable, Iterator, MutableSequence, Never, Optional, Protocol, Sequence, SupportsIndex, TypeVar, overload, runtime_checkable

from Viper.abc.utils import Budget
from .utils import Budget

__all__ = ["IOClosedError", "IOBase", "IOReader", "IOWriter", "IO"]





STREAM_PACKET_SIZE = 2 ** 20

T1 = TypeVar("T1", covariant=True)

@runtime_checkable
class Buffer(Protocol[T1], metaclass = ABCMeta):

    """
    An Abstract Base Class that represents object that behave like readable buffers.
    """

    @abstractmethod
    def __len__(self) -> int:
        """
        Implements len(self).
        """
        raise NotImplementedError
    
    @overload
    @abstractmethod
    def __getitem__(self, i : SupportsIndex) -> T1:
        ...
    
    @overload
    @abstractmethod
    def __getitem__(self, i : slice) -> Sequence[T1]:
        ...

    def __iter__(self) -> Iterator[T1]:
        """
        Implements iter(self).
        """
        return (self[i] for i in range(len(self)))





T2 = TypeVar("T2")

@runtime_checkable
class MutableBuffer(Protocol[T2], metaclass = ABCMeta):

    """
    An Abstract Base Class that represents object that behave like readable buffers.
    """

    @abstractmethod
    def __len__(self) -> int:
        """
        Implements len(self).
        """
        raise NotImplementedError
    
    @overload
    @abstractmethod
    def __getitem__(self, i : SupportsIndex) -> T2:
        ...
    
    @overload
    @abstractmethod
    def __getitem__(self, i : slice) -> MutableSequence[T2]:
        ...

    def __iter__(self) -> Iterator[T2]:
        """
        Implements iter(self).
        """
        return (self[i] for i in range(len(self)))
    
    @overload
    @abstractmethod
    def __setitem__(self, i : SupportsIndex, value : T2):
        ...

    @overload
    @abstractmethod
    def __setitem__(self, i : slice, value : Iterable[T2]):
        ...





class IOClosedError(Exception):

    """
    This exception indicates that an IO operation was tried on a closed stream.
    """





Buf = TypeVar("Buf", bound=Buffer)
MutBuf = TypeVar("MutBuf", bound=MutableBuffer)

class IOBase(Generic[Buf, MutBuf], metaclass = ABCMeta):

    """
    This class describes basic methods required for most types of streams interfaces.
    """

    @property
    @abstractmethod
    def lock(self) -> RLock:
        """
        This property should return a recursive lock for the thread to acquire the ressource.
        While the lock is held, not other thread should be able to use this stream.

        Use it if you want to perform operations that depend on the readable and writable properties.
        """
        raise NotImplementedError

    @abstractmethod
    def fileno(self) -> int:
        """
        If available, returns the file descriptor (integer) representing the underlying stream for the system.
        """
        raise NotImplementedError
    
    def isatty(self) -> bool:
        """
        Returns True if the stream is a tty-like stream. Default implementation uses fileno().
        """
        from os import isatty
        return isatty(self.fileno())

    @abstractmethod
    def close(self):
        """
        Closes the stream.
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def closed(self) -> bool:
        """
        Returns True if the stream has already been closed.
        """
        raise NotImplementedError
    
    @abstractmethod
    def tell(self) -> int:
        """
        Returns the current position in the stream (from the start).
        """
        raise NotImplementedError
    
    @abstractmethod
    def seekable(self) -> bool:
        """
        Returns true if the stream is seekable.
        """
        raise NotImplementedError
    
    def seek(self, offset : int, whence : int = SEEK_SET, /) -> int:
        """
        Seeks a position in stream. Position is calculated by adding offset to the reference point given by whence.
        - If whence = SEEK_SET = 0, seeks from the start of the stream. Offset should then be positive or zero.
        - If whence = SEET_CUR = 1, seeks from the current of the stream. Offset can be of any sign.
        - If whence = SEEK_END = 2, seeks from the end of the stream. Offset should be negative.
        """
        raise NotImplementedError("Unseekable stream")
    
    seek.__doc__ = f"""
        Seeks a position in stream. Position is calculated by adding offset to the reference point given by whence.
        - If whence = SEEK_SET = {SEEK_SET}, seeks from the start of the stream. Offset should then be positive or zero.
        - If whence = SEET_CUR = {SEEK_CUR}, seeks from the current of the stream. Offset can be of any sign.
        - If whence = SEEK_END = {SEEK_END}, seeks from the end of the stream. Offset should be negative.
        """
        
    @property
    @abstractmethod
    def readable(self) -> Budget:
        """
        Returns the amount of data that cen be immediately read from the stream.
        This should be a Budget object. Such objects are similar to semaphores, but anyone can increase them and you can lock the ressource even without reaching zero.

        About reading behavior of IO objects:
        - Trying to read less than or exactly this value should always work without blocking.
        - Trying to read more might block.
        - If this value is zero and the stream is closed, trying to read should raise an IOClosedError.
        - If this value is zero and the stream is not closed, data might become available for reading later.

        Note that you can await budget objects using the "with" statement:
        >>> with stream.readable as available:          # Should wait until stream.readable != 0 or stream.closed == True
        Using the "with" statement on this attribute should also acquire the read_lock of the stream.

        Note that it should not overestimate the readable data. When returning a large value by default, this value should be readable, not less.
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def writable(self) -> Budget:
        """
        Returns the amount of data that can be immediately written to the stream.
        This should be a Budget object. Such objects are similar to semaphores, but anyone can increase them and you can lock the ressource even without reaching zero.
        
        About writing behavior of IO objects:
        - Trying to write less than or exactly this value should always work without blocking.
        - Trying to write more might block.
        - If this value is zero and the stream is closed, trying to write should raise an IOClosedError.
        - If this value is zero and the stream is not closed, space might become available for writing later.

        Note that you can await budget objects using the "with" statement:
        >>> with stream.writable as available:          # Should wait until stream.writable != 0 or stream.closed == True
        Using the "with" statement on this attribute should also acquire the write_lock of the stream.

        Note that it should not overestimate the writable data. When returning a large value by default, this value should be writable, not less.
        """
        raise NotImplementedError
    
    def __del__(self):
        """
        Implements destruction of self. Closes stream by default.
        """
        self.close()

    def __enter__(self):
        """
        Implements with self.
        """
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Implements with self.
        """
        self.close()





R = TypeVar("R", bound="IOReader")

class IOReader(IOBase, Generic[Buf, MutBuf]):

    """
    This class describes an interface for reading from a stream.
    """

    @property
    def read_lock(self) -> RLock:
        """
        An alias for self.lock.
        """
        return self.lock
    
    @property
    def writable(self) -> Budget:
        from .utils import Budget
        return Budget(0)
    
    @abstractmethod
    def read(self, size : int | float = float("inf"), /) -> Buf:
        """
        Reads size pieces of data. If size is float("inf"), then reads as much data as possible.
        Will block until enough data is available.
        If the stream closes while waiting, it should return the remaining data or empty data.
        Use with the "readable" attribute to predict its behavior.
        Should raise IOClosedError when trying to read from a closed stream.
        """
        raise NotImplementedError
    
    @abstractmethod
    def readinto(self, buffer : MutBuf, /) -> int:
        """
        Same as read, but reads data into pre-allocated buffer (of a given size) and returns the amount of data read.
        """
        raise NotImplementedError
    
    @abstractmethod
    def readline(self, size : int | float = float("inf"), /) -> Buf:
        """
        Same as read, but will stop if a newline (included) is encountered while reading.
        """
        raise NotImplementedError
    
    def readlines(self, size : int | float = float("inf"), /) -> list[Buf]:
        """
        Same as readline, but reads multiple lines and returns a list of lines.
        """
        if not isinstance(size, int | float):
            raise TypeError(f"Expected int or float, got '{type(size).__name__}'")
        if (not isinstance(size, int) and size != float("inf")) or size < 0:
            raise ValueError(f"Expected positive integer or float('inf'), got {size}")
        
        n = 0
        lines = []
        with self.read_lock:
            while n < size:
                line = self.readline(max(size - n, -1))
                n += len(line)
                lines.append(line)
        return lines
    
    def __iter__(self) -> Iterator[Buf]:
        """
        Implements iter(self). Yields successive lines.
        """
        line = True
        with self.read_lock:
            while line:
                try:
                    line = self.readline()
                    yield line
                except IOClosedError:
                    break

    @overload
    def __rshift__(self, buffer : "IOWriter[Buf, MutBuf]") -> None:
        ...

    @overload
    def __rshift__(self : R, buffer : MutBuf) -> R:
        ...

    def __rshift__(self, buffer):
        """
        Implements self >> buffer.
        Acts like C++ flux operators.
        If the second operand is an instance of IOWriter, it will write to it until no data is available from self.read().
        """
        # if isinstance(buffer, IOWriter):
        #     with self.read_lock, buffer.write_lock:
        #         while True:
        #             available_for_write = min(buffer.writable, STREAM_PACKET_SIZE)
        #             available_for_read = min(self.readable, STREAM_PACKET_SIZE)
        #             if not available_for_read:
        #                 if self.closed:
        #                     return
        #                 self.read(0)
        #                 available_for_read = min(self.readable, STREAM_PACKET_SIZE)
        #                 if not available_for_read:
        #                     return
        #             if not available_for_write:
        #                 if buffer.closed:
        #                     return
        #                 available_for_write = 1
        #             packet = self.read(min(available_for_write, available_for_read))
        #             if buffer.closed:
        #                 raise RuntimeError("Could not write all data to the destination stream")
        #             n = buffer.write(packet)
        #             while n < len(packet):
        #                 if buffer.closed:
        #                     raise RuntimeError("Could not write all data to the destination stream")
        #                 n += buffer.write(packet[n:])
        # else:
        try:
            self.readinto(buffer)
            return self
        except TypeError:
            return buffer << self
        
    @overload
    def __rlshift__(self, buffer : "IOWriter[Buf, MutBuf]") -> None:
        ...

    @overload
    def __rlshift__(self : R, buffer : MutBuf) -> R:
        ...
    
    def __rlshift__(self, buffer):
        """
        Implements buffer << self.
        Acts like C++ flux operators.
        If the second operand is an instance of IOWriter, it will write to it until no data is available from self.read().
        """
        return self >> buffer





W = TypeVar("W", bound="IOWriter")

class IOWriter(IOBase, Generic[Buf, MutBuf]):
    
    """
    This class describes an interface for writing to a stream.
    """

    @property
    def write_lock(self) -> RLock:
        """
        An alias for self.lock.
        """
        return self.lock
    
    @property
    def readable(self) -> Budget:
        from .utils import Budget
        return Budget(0)

    def flush(self):
        """
        Flushes the write buffers of the stream if applicable. Does nothing by default.
        """
        if self.closed:
            raise IOClosedError("Cannot flush closed stream")

    @abstractmethod
    def truncate(self, size : Optional[int] = None, /):
        """
        Changes stream size, adding null data if size is bigger than current size. By default, resizes to the current position. Position in stream should not change.
        """
        raise NotImplementedError

    @abstractmethod
    def write(self, data : Buf, /) -> int:
        """
        Writes as much of data to the stream. Returns the amount of data written.
        Will wait to write all of data (it should block until space is available for writing even if the data provided is empty).
        If the stream closes while waiting, returns the amount of data that could be successfully written before that.
        Use with the "writable" attribute to predict its behavior.
        Should raise IOClosedError when attempting to write to a closed stream.
        """
        raise NotImplementedError
    
    def writelines(self, lines : Iterable[Buf], /) -> int:
        """
        Writes all the lines in the given iterable.
        Stops if one of the lines cannot be written entirely.
        Does not add newlines at the end of each line.
        Returns the amount of data written.
        """
        from typing import Iterable
        if not isinstance(lines, Iterable):
            raise TypeError("Expected iterable, got " + repr(type(lines).__name__))
        n = 0
        with self.lock:
            for line in lines:
                try:
                    ni = self.write(line)
                except TypeError as e:
                    raise e from None
                n += ni
                if ni < len(line):
                    break
        return n
    
    @overload
    def __lshift__(self : W, buffer : Buf) -> W:
        ...

    @overload
    def __lshift__(self, buffer : IOReader[Buf, MutBuf]) -> None:
        ...
    
    def __lshift__(self, buffer):
        """
        Implements self << buffer.
        Acts like C++ flux operators.
        If the second operand is an instance of IOReader, it will read from it until no data is available from buffer.read().
        """
        if isinstance(buffer, IOReader):
            available_for_read, available_for_write = 0, 0
            acquired_reader, acquired_writer = False, False
            with self.write_lock, buffer.read_lock:
                while True:

                    try:

                        acquired_reader, acquired_writer = False, False
                        while not acquired_reader or not acquired_writer:

                            if not acquired_reader:
                                acquired_reader = buffer.readable.acquire(timeout=0.001)

                            if acquired_reader:
                                available_for_read = buffer.readable.value
                                if not available_for_read:
                                    if not buffer.closed:
                                        raise RuntimeError("Reading stream acquired with no data available and is not closed")
                                    return
                                
                            if not acquired_writer:
                                acquired_writer = self.writable.acquire(timeout=0.001)

                            if acquired_writer:
                                available_for_write = self.writable.value
                                if not available_for_write:
                                    if not self.closed:
                                        raise RuntimeError("Writing stream acquired with no space available and is not closed")
                                    return

                        available_for_write = min(available_for_write, STREAM_PACKET_SIZE)
                        available_for_read = min(available_for_read, STREAM_PACKET_SIZE)

                        packet = buffer.read(min(available_for_write, available_for_read))
                        n = self.write(packet)
                        if n < len(packet):
                            raise RuntimeError("Could not write all data to writing stream whereas it guaranteed it would fit")
                        
                    finally:
                        if acquired_reader:
                            buffer.readable.release()
                        if acquired_writer:
                            self.writable.release()
                            
        else:
            try:
                n = 0
                while n < len(buffer):
                    n += self.write(buffer[n:])
                return self
            except TypeError:
                return NotImplemented
    
    @overload
    def __rrshift__(self : W, buffer : Buf) -> W:
        ...

    @overload
    def __rrshift__(self, buffer : IOReader[Buf, MutBuf]) -> None:
        ...

    def __rrshift__(self, buffer):
        """
        Implements buffer >> self.
        Acts like C++ flux operators.
        If the second operand is an instance of IOReader, it will read from it until no data is available from buffer.read().
        """
        return self << buffer
    




class IO(IOReader[Buf, MutBuf], IOWriter[Buf, MutBuf]):

    """
    This class describes an interface for complete IO interactions with a stream.
    """

    @property
    @abstractmethod
    def readable(self) -> Budget:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def writable(self) -> Budget:
        raise NotImplementedError

    class LockGroup:

        """
        This class is used to create a group of locks that behave like one.
        Acquiering the group will acquire all the locks one after the other.
        Same for releasing.
        """

        from threading import Lock, RLock
        __types = (type(Lock()), type(RLock()))
        del Lock, RLock

        def __init__(self, *locks : "Lock | RLock") -> None:
            for l in locks:
                if not isinstance(l, self.__types):
                    raise TypeError(f"Expected lock-like object, got '{type(l).__name__}'")
            self.__locks = locks
        
        @property
        def locks(self):
            """
            The tuple of locks that this lock group holds.
            """
            return self.__locks
        
        def acquire(self, blocking : bool = True, timeout : float = float("inf")) -> bool:
            """
            Acquires the group of locks.
            """
            try:
                timeout = float(timeout)
            except:
                pass
            if not isinstance(blocking, bool):
                raise TypeError(f"Expected bool for blocking, got '{type(blocking).__name__}'")
            if not isinstance(timeout, float):
                raise TypeError(f"Expected float for timeout, got '{type(timeout).__name__}'")
            if timeout < 0:
                raise ValueError(f"Expected positive value for timeout, got {timeout}")
            
            if timeout == float("inf"):
                for i, li in enumerate(self.locks):
                    try:
                        ok = li.acquire(blocking=blocking)
                    except:
                        for j, lj in enumerate(self.locks):
                            if j >= i:
                                break
                            lj.release()
                        raise
                    if not ok:
                        for j, lj in enumerate(self.locks):
                            if j >= i:
                                break
                            lj.release()
                        return False
                return True

            else:
                from time import time
                t = time()
                for i, li in enumerate(self.locks):
                    t_i = time()
                    timeout -= t_i - t
                    t = t_i
                    if timeout < 0:
                        return False
                    try:
                        ok = li.acquire(blocking=blocking, timeout=timeout)
                    except:
                        for j, lj in enumerate(self.locks):
                            if j >= i:
                                break
                            lj.release()
                        raise
                    if not ok:
                        for j, lj in enumerate(self.locks):
                            if j >= i:
                                break
                            lj.release()
                        return False
                return True
        
        def release(self):
            """
            Releases the group of locks.
            """
            for l in self.locks:
                l.release()

        def __enter__(self):
            """
            Implements with self.
            """
            self.acquire()
        
        def __exit__(self, exc_type, exc_value, traceback):
            """
            Implements with self.
            """
            self.release()

    @property
    @abstractmethod
    def read_lock(self) -> RLock:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def write_lock(self) -> RLock:
        raise NotImplementedError

    @property
    def lock(self) -> "RLock | LockGroup":
        """
        Returns a lock group of the read lock and the write lock if they are different.
        Subclasses may create different read and write locks if meaningful.
        """
        rl = self.read_lock
        wl = self.write_lock
        if rl != wl:
            return self.LockGroup(rl, wl)
        return rl





class BytesIOBase(IOBase[bytes | bytearray | memoryview, bytearray | memoryview]):
    """
    The abstract base class for byte streams.
    """
class BytesReader(IOReader[bytes | bytearray | memoryview, bytearray | memoryview]):
    """
    The abstract base class for byte reading streams.
    """
class BytesWriter(IOWriter[bytes | bytearray | memoryview, bytearray | memoryview]):
    """
    The abstract base class for writing streams.
    """
class BytesIO(BytesReader, BytesWriter, IO[bytes | bytearray | memoryview, bytearray | memoryview]):
    """
    The abstract base class for byte reading and writing streams.
    """

__all__ += ["BytesIOBase", "BytesReader", "BytesWriter", "BytesIO"]

class StringIOBase(IOBase[str, Never]):
    """
    The abstract base class for text streams.
    """
class StringReader(StringIOBase, IOReader[str, Never]):
    """
    The abstract base class for text reading streams.
    """
    def readinto(self, buffer) -> Never:
        """
        Do not use: cannot write in buffer in text mode.
        """
        raise ValueError("Cannot use readinto with text streams")
class StringWriter(StringIOBase, IOWriter[str, Never]):
    """
    The abstract base class for text writing streams.
    """
class StringIO(StringReader, StringWriter, IO[str, Never]):
    """
    The abstract base class for text reading and writing streams.
    """

__all__ += ["StringIOBase", "StringReader", "StringWriter", "StringIO"]





del ABCMeta, abstractmethod, SEEK_CUR, SEEK_END, SEEK_SET, Generic, Iterable, Iterator, MutableSequence, Never, Optional, Protocol, Sequence, SupportsIndex, TypeVar, overload, W, R, MutBuf, Buf, T2, T1, RLock