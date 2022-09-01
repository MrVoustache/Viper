"""
This module stores multiple simpler interfaces for stream manipulation.
"""

from abc import ABCMeta, abstractmethod
from io import SEEK_CUR, SEEK_END, SEEK_SET
from typing import Iterable, Iterator, Optional

__all__ = ["IOClosedError", "BytesIOBase", "BytesReader", "BytesWriter", "BytesIO"]





class IOClosedError(Exception):

    """
    This exception indicates that an IO operation was tried on a closed stream.
    """




class BytesIOBase(metaclass = ABCMeta):

    """
    This class describes basic methods required for most types of streams interfaces.
    """

    @abstractmethod
    def fileno(self) -> int:
        """
        If available, returns the file descriptor (integer) representing the underlying stream for the system.
        """
        raise NotImplementedError()
    
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
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def closed(self):
        """
        Returns True if the stream has already been closed.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def tell(self) -> int:
        """
        Returns the current position in the stream (from the start).
        """
        raise NotImplementedError()
    
    @abstractmethod
    def seekable(self) -> bool:
        """
        Returns true if the stream is seekable.
        """
        raise NotImplementedError()
    
    def seek(self, offset : int, whence : int = SEEK_SET, /):
        raise NotImplementedError("Unseekable stream")
    
    seek.__doc__ = """
        Seeks a position in stream. Position is calculated by adding offset to the reference point given by whence.
        - If whence = SEEK_SET = {}, seeks from the start of the stream. Offset should then be positive or zero.
        - If whence = SEET_CUR = {}, seeks from the current of the stream. Offset can be of any sign.
        - If whence = SEEK_END = {}, seeks from the end of the stream. Offset should be negative.
        """.format(SEEK_SET, SEEK_CUR, SEEK_END)
    
    @abstractmethod
    def readable(self) -> bool:
        """
        Returns True if the stream can be read from (i.e. has at least a read() method).
        """
        raise NotImplementedError()
    
    @abstractmethod
    def writable(self) -> bool:
        """
        Returns True is the stream can be written to (i.e. has at least a write() method).
        """
        raise NotImplementedError()
    
    def __del__(self):
        """
        Implements destruction of self. Closes stream by default.
        """
        self.close()




class BytesReader(BytesIOBase):

    """
    This class describes an interface for reading from a bytes stream.
    """

    @abstractmethod
    def read_blocking(self) -> bool:
        """
        Returns True if the stream can block on reading when no bytes are available.
        """
        raise NotImplementedError()

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    @abstractmethod
    def read(self, size : int = -1, /) -> bytes:
        """
        Reads size bytes. If size is -1, then reads as many bytes as possible.
        If not blocking and no bytes are available, returns empty bytes.
        If blocking and no bytes are available, it should block until size bytes are available.
        If the stream closes while waiting, it should return the remaining bytes or empty bytes too.
        Should raise IOClosedError when trying to read from a closed stream.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def readinto(self, buffer : bytearray | memoryview, /) -> int:
        """
        Same as read, but reads data into pre-allocated buffer (of a given size) and returns the number of bytes read.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def readline(self, size : int = -1, /) -> bytes:
        """
        Same as read, but will stop if b"\n" (newline included) is encountered while reading.
        """
        raise NotImplementedError()
    
    def readlines(self, size : int = -1, /) -> list[bytes]:
        """
        Same as readline, but reads multiple lines and returns a list of lines.
        """
        n = 0
        lines = []
        while n < size:
            line = self.readline(max(size - n, -1))
            n += len(line)
            lines.append(line)
        return lines
    
    def __iter__(self) -> Iterator[bytes]:
        """
        Implements iter(self). Yields successive lines.
        """
        line = True
        while line:
            line = self.readline()
            yield line
    
    @abstractmethod
    async def aread(self, size : int = -1, /) -> bytes:
        """
        Asynchronous version of read.
        Should wait only if read would block.
        Should also handle its own loop is necessary. (See async_utils.SelectorLoop/ProactorLoop for more info)
        """
        raise NotImplementedError()

    @abstractmethod
    async def areadinto(self, buffer : bytearray | memoryview, /) -> int:
        """
        Same as aread, but reads data into pre-allocated buffer (of a given size) and returns the number of bytes read.
        """
        raise NotImplementedError()




class BytesWriter(BytesIOBase):
    
    """
    This class describes an interface for writing to a bytes stream.
    """

    @abstractmethod
    def write_blocking(self) -> bool:
        """
        Returns True if the stream can block on writing when no bytes can be written.
        """
        raise NotImplementedError()

    def writable(self) -> bool:
        return True

    def readable(self) -> bool:
        return False

    def flush(self):
        """
        Flushes the write buffers of the stream if applicable. Does nothing by default.
        """
        if self.closed:
            raise IOClosedError("Cannot flush closed stream")

    @abstractmethod
    def truncate(self, size : Optional[int] = None, /):
        """
        Changes stream size, adding zero bytes if size is bigger than current size. By default, resizes to the current position. Position in stream should not change.
        """
        raise NotImplementedError()

    @abstractmethod
    def write(self, data : bytes | bytearray | memoryview, /) -> int:
        """
        Writes as much of data to the stream. Returns the number of bytes written.
        If not blocking, returns the number of bytes successfully written, even if no bytes could be written.
        If blocking, waits to write all of data.
        If the stream closes while waiting, returns the number of bytes that could be successfully written before that.
        Should raise IOClosedError when attempting to write to a closed stream.
        """
        raise NotImplementedError()
    
    def writelines(self, lines : Iterable[bytes | bytearray | memoryview], /) -> int:
        """
        Writes all the lines in the given iterable.
        Stops if one of the lines cannot be written entirely.
        Does not add b"\n" at the end of each line.
        Returns the number of bytes written.
        """
        from typing import Iterable
        if not isinstance(lines, Iterable):
            raise TypeError("Expected iterable, got " + repr(type(lines).__name__))
        n = 0
        for line in lines:
            if not isinstance(line, bytes | bytearray | memoryview):
                raise TypeError("Expected iterable of bytes, bytearray or memoriview, got " + repr(type(line).__name__))
            ni = self.write(line)
            n += ni
            if ni < len(line):
                break
        return n
    
    @abstractmethod
    async def awrite(self, data : bytes | bytearray | memoryview, /) -> int:
        """
        Asynchronous version of write.
        Should wait only if write would block.
        Should also handle its own loop is necessary. (See async_utils.SelectorLoop/ProactorLoop for more info)
        """
        raise NotImplementedError()




class BytesIO(BytesReader, BytesWriter):

    """
    This class describes an interface for complete IO interactions with a bytes stream.
    """

    def readable(self) -> bool:
        return True
    
    def writable(self) -> bool:
        return True



del ABCMeta, abstractmethod, SEEK_CUR, SEEK_END, SEEK_SET, Iterable, Iterator, Optional