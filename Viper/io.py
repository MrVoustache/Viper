"""
This module adds some useful IO tools.
"""

from io import SEEK_SET
from threading import RLock
from .abc.io import BytesIO as AbstractBytesIO

__all__ = ["BytesIO"]





class BytesIO(AbstractBytesIO):

    """
    A subclass of Viper.abc.io.BytesIO that uses an internal buffer to act as a bytes stream. IO version of a bytearray.
    They are not limited in size and thus do not block on writing.

    They are thread-safe.
    """

    def __init__(self, initial_data : bytes | bytearray | memoryview = b"") -> None:
        if not isinstance(initial_data, bytes | bytearray | memoryview):
            raise TypeError(f"Expected readable buffer, got '{type(initial_data).__name__}'")
        super().__init__()
        from threading import RLock
        self.__buffer = bytearray(initial_data)
        self.__pos : int = 0
        self.__closed : bool = False
        self.__lock = RLock()

    @property
    def lock(self) -> RLock:
        return self.__lock
    
    @property
    def readable(self) -> int | float:
        return max(0, len(self.__buffer) - self.__pos)
    
    @property
    def writable(self) -> int | float:
        return float("inf")

    def fileno(self) -> int:
        raise OSError("BytesIO objects are not associated to any system object.")
    
    def close(self):
        with self.lock:
            self.__closed = True

    @property
    def closed(self) -> bool:
        return self.__closed
    
    def tell(self) -> int:
        return self.__pos
    
    def seekable(self) -> bool:
        return True
    
    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if not isinstance(offset, int) or not isinstance(whence, int):
            raise TypeError(f"Expected int, int, got '{type(offset).__name__}' and '{type(whence).__name__}'")
        from io import SEEK_SET, SEEK_CUR, SEEK_END
        if whence not in (SEEK_SET, SEEK_CUR, SEEK_END):
            raise ValueError(f"invalid whence ({whence}, should be {SEEK_SET}, {SEEK_CUR} or {SEEK_END})")
        if whence == SEEK_SET:
            self.__pos = offset
        elif whence == SEEK_CUR:
            self.__pos += offset
        else:
            self.__pos = len(self.__buffer) + offset
        return self.__pos
    
    def write_blocking(self) -> bool:
        return False
    
    def truncate(self, size: int | None = None):
        if size is None:
            size = self.__pos
        if not isinstance(size, int):
            raise TypeError(f"Expected int or None, got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        with self.lock:
            if len(self.__buffer) < size:
                self.__buffer.extend(b"\0" * (size - len(self.__buffer)))
            elif len(self.__buffer) > size:
                self.__buffer = self.__buffer[:size]

    def write(self, data: bytes | bytearray | memoryview) -> int:
        if not isinstance(data, bytes | bytearray | memoryview):
            raise TypeError(f"Expected readable buffer, got '{type(data).__name__}'")
        with self.lock:
            if self.__pos > len(self.__buffer):
                self.__buffer.extend(b"\0" * (self.__pos - len(self.__buffer)))
            self.__buffer[self.__pos : self.__pos + len(data)] = data
            self.__pos += len(data)
            return len(data)
    
    def read_blocking(self) -> bool:
        return False
    
    def read(self, size: int = -1) -> bytes:
        if not isinstance(size, int):
            raise TypeError(f"Expected int, got '{type(size).__name__}'")
        if size < -1:
            raise ValueError(f"Expected integer >= -1, got {size}")
        if size == -1:
            total_size = float("inf")
        else:
            total_size = size
        with self.lock:
            data = bytes(self.__buffer[self.__pos : min(len(self.__buffer), self.__pos + total_size)])
            self.__pos += len(data)
            return data
        
    def readinto(self, buffer: bytearray | memoryview) -> int:
        if not isinstance(buffer, bytearray | memoryview):
            raise TypeError(f"Expected writable buffer, got '{type(buffer).__name__}'")
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)
    
    def readline(self, size: int = -1) -> bytes:
        if not isinstance(size, int):
            raise TypeError(f"Expected int, got '{type(size).__name__}'")
        if size < -1:
            raise ValueError(f"Expected integer >= -1, got {size}")
        if size == -1:
            total_size = float("inf")
        else:
            total_size = size
        with self.lock:
            try:
                i = self.__buffer.index(b"\n", self.__pos, min(len(self.__buffer), self.__pos + total_size))        # type: ignore Until we have Literal inf...
                data = bytes(memoryview(self.__buffer)[self.__pos : i + 1])
            except ValueError:
                data = bytes(memoryview(self.__buffer)[self.__pos : min(len(self.__buffer), self.__pos + total_size)])
            self.__pos += len(data)
            return data





del SEEK_SET, AbstractBytesIO, RLock