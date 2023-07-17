"""
This module stores multiple simpler interfaces for stream manipulation.
"""

from abc import ABCMeta, abstractmethod
from io import SEEK_CUR, SEEK_END, SEEK_SET
from threading import RLock
from typing import Generic, Iterable, Iterator, MutableSequence, Never, Optional, Protocol, Sequence, SupportsIndex, TypeVar, overload, runtime_checkable

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
    def readable(self) -> int | float:
        """
        Returns the amount of data that cen be immediately read from the stream.
        Should be a positive integer or float("inf").
        """
        return 0
    
    @property
    def writable(self) -> int | float:
        """
        Returns the amount of data that can be immediately written to the stream.
        Should be a positive integer or float("inf").
        """
        return 0
    
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

    @abstractmethod
    def read_blocking(self) -> bool:
        """
        Returns True if the stream can block on reading when no data are available.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def readable(self) -> int | float:
        raise NotImplementedError
    
    @abstractmethod
    def read(self, size : int | float = float("inf"), /) -> Buf:
        """
        Reads size pieces of data. If size is float("inf"), then reads as much data as possible.
        If not blocking and no data is available, returns empty data.
        If blocking and no data is available, it should block until enough data is available.
        If the stream closes while waiting, it should return the remaining data or empty data. It should return empty data at least once when closed.
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
        with self.lock:
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
        with self.lock:
            while line:
                line = self.readline()
                yield line

    @overload
    def __rshift__(self : R, buffer : MutBuf) -> R:
        pass

    @overload
    def __rshift__(self, buffer : "IOWriter[Buf, MutBuf]") -> None:
        pass

    def __rshift__(self, buffer):
        """
        Implements self >> buffer.
        Acts like C++ flux operators.
        If the second operand is an instance of IOWriter, it will write to it until no data is available from self.read().
        """
        if isinstance(buffer, IOWriter):
            with self.lock, buffer.lock:
                packet = True
                while packet:
                    available = min(buffer.writable, STREAM_PACKET_SIZE)
                    packet = self.read(available)
                    n = buffer.write(packet)
                    assert n == len(packet), "Could not write packet entirely into destination buffer"
        else:
            try:
                self.readinto(buffer)
                return self
            except TypeError:
                return NotImplemented
    
    def __rlshift__(self : R, buffer : MutBuf) -> R:
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

    @abstractmethod
    def write_blocking(self) -> bool:
        """
        Returns True if the stream can block on writing when no data can be written.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def writable(self) -> int | float:
        raise NotImplementedError

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
        If not blocking, returns the amount of data successfully written, even if no data could be written.
        If blocking, waits to write all of data.
        If the stream closes while waiting, returns the amount of data that could be successfully written before that.
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
        pass
    
    def __lshift__(self, buffer):
        """
        Implements self << buffer.
        Acts like C++ flux operators.
        If the second operand is an instance of IOReader, it will read from it until no data is available from buffer.read().
        """
        if isinstance(buffer, IOReader):
            with self.lock, buffer.lock:
                packet = True
                while packet:
                    available = min(self.writable, STREAM_PACKET_SIZE)
                    packet = buffer.read(available)
                    n = self.write(packet)
                    assert n == len(packet), "Could not write packet entirely into destination buffer"
        else:
            try:
                n = 0
                while n < len(buffer):
                    n += self.write(buffer[n:])
                return self
            except TypeError:
                return NotImplemented
    
    def __rrshift__(self : W, buffer : Buf | IOReader[Buf, MutBuf]) -> W:
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

class StringIOBase(IOBase[str, bytearray | memoryview]):
    """
    The abstract base class for text streams.
    """
class StringReader(StringIOBase, IOReader[str, bytearray | memoryview]):
    """
    The abstract base class for text reading streams.
    """
    def readinto(self, buffer) -> Never:
        """
        Do not use: cannot write in buffer in text mode.
        """
        raise ValueError("Cannot use readinto with text streams")
class StringWriter(StringIOBase, IOWriter[str, bytearray | memoryview]):
    """
    The abstract base class for text writing streams.
    """
class StringIO(StringReader, StringWriter, IO[str, bytearray | memoryview]):
    """
    The abstract base class for text reading and writing streams.
    """

__all__ += ["StringIOBase", "StringReader", "StringWriter", "StringIO"]





del ABCMeta, abstractmethod, SEEK_CUR, SEEK_END, SEEK_SET, Generic, Iterable, Iterator, MutableSequence, Never, Optional, Protocol, Sequence, SupportsIndex, TypeVar, overload, W, R, MutBuf, Buf, T2, T1, RLock