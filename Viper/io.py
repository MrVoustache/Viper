"""
This module adds some useful IO tools. This includes IO buffer and pipe/circular buffers for both bytes and strings.
"""

from io import SEEK_SET
from threading import RLock
from typing import Generator, Iterator
from .abc.io import BytesIO as AbstractBytesIO, StringIO as AbstractStringIO

__all__ = ["BytesIO", "StringIO", "BytesBuffer", "StringBuffer"]





BUFFER_SIZE = 2 ** 20

class BytesIO(AbstractBytesIO):

    """
    A subclass of Viper.abc.io.BytesIO that uses an internal buffer to act as a bytes stream. IO version of a bytearray.
    They are not limited in size and thus do not block on writing.

    They are thread-safe.
    """

    from .abc.io import IOClosedError as __IOClosedError

    __slots__ = {
        "__buffer" : "The internal buffer storing the stream.",
        "__pos" : "The current cursor pos in the stream.",
        "__closed" : "A boolean indicating if the stream has been closed.",
        "__readable" : "The readable Budget.",
        "__writable" : "The writable Budget."
    }

    def __init__(self, initial_data : bytes | bytearray | memoryview = b"") -> None:
        if not isinstance(initial_data, bytes | bytearray | memoryview):
            raise TypeError(f"Expected readable buffer, got '{type(initial_data).__name__}'")
        super().__init__()
        from .abc.utils import Budget
        from .abc.io import STREAM_PACKET_SIZE
        self.__buffer = bytearray(initial_data)
        self.__pos : int = 0
        self.__closed : bool = False
        self.__readable = Budget()
        self.__writable = Budget(STREAM_PACKET_SIZE)
    
    @property
    def readable(self):
        return self.__readable
    
    @property
    def writable(self):
        return self.__writable

    def fileno(self) -> int:
        raise OSError("BytesIO objects are not associated to any system object.")
    
    def close(self):
        self.__closed = True
        self.__writable.close()
        self.__readable.close()

    @property
    def closed(self) -> bool:
        return self.__closed
    
    def tell(self) -> int:
        if self.closed:
            raise self.__IOClosedError(f"{type(self).__name__} is closed")
        return self.__pos
    
    def seekable(self) -> bool:
        return True
    
    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if not isinstance(offset, int) or not isinstance(whence, int):
            raise TypeError(f"Expected int, int, got '{type(offset).__name__}' and '{type(whence).__name__}'")
        from io import SEEK_SET, SEEK_CUR, SEEK_END
        if whence not in (SEEK_SET, SEEK_CUR, SEEK_END):
            raise ValueError(f"invalid whence ({whence}, should be {SEEK_SET}, {SEEK_CUR} or {SEEK_END})")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            if whence == SEEK_SET:
                pos = offset
            elif whence == SEEK_CUR:
                pos = self.__pos + offset
            else:
                pos = len(self.__buffer) + offset
            if pos < 0:
                raise ValueError("Negative position in stream.")
            self.__pos = pos
            self.__readable.value = len(self.__buffer) - self.__pos
            return self.__pos
    
    def truncate(self, size: int | None = None):
        if size is None:
            size = self.__pos
        if not isinstance(size, int):
            raise TypeError(f"Expected int or None, got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            if len(self.__buffer) < size:
                self.__buffer.extend(b"\0" * (size - len(self.__buffer)))
                self.__readable.value = len(self.__buffer) - self.__pos
            elif len(self.__buffer) > size:
                self.__buffer = self.__buffer[:size]
                self.__readable.value = len(self.__buffer) - self.__pos

    def write(self, data: bytes | bytearray | memoryview) -> int:
        if not isinstance(data, bytes | bytearray | memoryview):
            raise TypeError(f"Expected readable buffer, got '{type(data).__name__}'")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            if self.__pos > len(self.__buffer):
                self.__buffer.extend(b"\0" * (self.__pos - len(self.__buffer)))
            self.__buffer[self.__pos : self.__pos + len(data)] = data
            self.__pos += len(data)
            self.__readable.value = len(self.__buffer) - self.__pos
            return len(data)
    
    def read(self, size: int | float = float("inf")) -> bytes:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        else:
            total_size = size
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            data = bytes(self.__buffer[self.__pos : min(len(self.__buffer), self.__pos + total_size)])
            self.__pos += len(data)
            self.__readable.value = len(self.__buffer) - self.__pos
            return data
        
    def readinto(self, buffer: bytearray | memoryview) -> int:
        if not isinstance(buffer, bytearray | memoryview):
            raise TypeError(f"Expected writable buffer, got '{type(buffer).__name__}'")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            data = self.read(len(buffer))
            buffer[:len(data)] = data
            return len(data)
    
    def readline(self, size: int | float = float("inf")) -> bytes:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        else:
            total_size = size
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            try:
                i = self.__buffer.index(b"\n", self.__pos, min(len(self.__buffer), self.__pos + total_size))        # type: ignore Until we have Literal inf...
                data = bytes(memoryview(self.__buffer)[self.__pos : i + 1])
            except ValueError:
                data = bytes(memoryview(self.__buffer)[self.__pos : min(len(self.__buffer), self.__pos + total_size)])
            self.__pos += len(data)
            self.__readable.value = len(self.__buffer) - self.__pos
            return data
        




class StringIO(AbstractStringIO):

    """
    A subclass of Viper.abc.io.StringIO that uses an internal buffer to act as a string stream. IO str version of a bytearray.
    They are not limited in size and thus do not block on writing.

    They are thread-safe.
    """

    from .abc.io import IOClosedError as __IOClosedError

    __slots__ = {
        "__buffer" : "The internal buffer storing the stream.",
        "__bytes_pos" : "The current cursor pos in the stream.",
        "__str_pos" : "The current position in the Unicode domain.",
        "__closed" : "A boolean indicating if the stream has been closed.",
        "__readable" : "The readable Budget.",
        "__writable" : "The writable Budget.",
        "__str_len" : "The size of the stream in the Unicode domain."
    }

    def __init__(self, initial_data : str = "") -> None:
        if not isinstance(initial_data, str):
            raise TypeError(f"Expected str, got '{type(initial_data).__name__}'")
        super().__init__()
        from .abc.utils import Budget
        from .abc.io import STREAM_PACKET_SIZE
        self.__buffer = bytearray(initial_data.encode())
        self.__bytes_pos : int = 0
        self.__str_pos : int = 0
        self.__closed : bool = False
        self.__str_len : int = len(initial_data)
        self.__readable = Budget()
        self.__writable = Budget(STREAM_PACKET_SIZE)

    def __parallel_walker(self, start : int = 0) -> Iterator[tuple[int, int]]:
        """
        Yields pairs of integers indicating the position of the cursor in the buffer in the encoded domain and in the decoded domain.
        Usually, for all (i, j) in self.__parallel_walker, i >= j and i - j is an increasing function.
        """
        from codecs import getincrementaldecoder
        decoder = getincrementaldecoder("utf-8")()
        decoder.reset()
        buffer = memoryview(self.__buffer)[start:]
        j = -1
        last_i = 0
        with self.lock:
            for i in range(len(buffer)):
                byte = bytes(buffer[i : i + 1])
                try:
                    s = decoder.decode(byte)
                    if s:
                        j += 1
                        # print(f"Decoded byte {byte} as '{s}'")
                        yield last_i, j
                        last_i = i + 1
                    # else:
                    #     print(f"Decoding byte {byte}")
                except BaseException as e:
                    # print(f"Faulting ({type(e)}) byte : {byte}")
                    raise

    def __str_pos_to_bytes_pos(self, str_pos : int) -> int:
        """
        Given a Unicode character position in the buffer, returns the corresponding encoded position.
        (i.e. converts positions from str domain to bytes domain)
        """
        if str_pos >= self.__str_len:
            bytes_pos = len(self.__buffer) + (str_pos - self.__str_len)
        elif str_pos >= self.__str_pos:
            for i_bytes_pos, i_str_pos in self.__parallel_walker(self.__bytes_pos):
                if self.__str_pos + i_str_pos == str_pos:
                    bytes_pos = self.__bytes_pos + i_bytes_pos
                    break
            else:
                raise RuntimeError("Got lost in the encoding...")
        else:
            for i_bytes_pos, i_str_pos in self.__parallel_walker():
                if i_str_pos == str_pos:
                    bytes_pos = i_bytes_pos
                    break
            else:
                raise RuntimeError("Got lost in the encoding...")
        return bytes_pos
    
    @property
    def readable(self):
        return self.__readable
    
    @property
    def writable(self):
        return self.__writable

    def fileno(self) -> int:
        raise OSError("StringIO objects are not associated to any system object.")
    
    def close(self):
        self.__closed = True
        self.__writable.close()
        self.__readable.close()

    @property
    def closed(self) -> bool:
        return self.__closed
    
    def tell(self) -> int:
        if self.closed:
            raise self.__IOClosedError(f"{type(self).__name__} is closed")
        return self.__str_pos
    
    def seekable(self) -> bool:
        return True
    
    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if not isinstance(offset, int) or not isinstance(whence, int):
            raise TypeError(f"Expected int, int, got '{type(offset).__name__}' and '{type(whence).__name__}'")
        from io import SEEK_SET, SEEK_CUR, SEEK_END
        if whence not in (SEEK_SET, SEEK_CUR, SEEK_END):
            raise ValueError(f"invalid whence ({whence}, should be {SEEK_SET}, {SEEK_CUR} or {SEEK_END})")
        
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            if whence == SEEK_SET:
                final_str_pos = offset
            elif whence == SEEK_CUR:
                final_str_pos = self.__str_pos + offset
            else:
                final_str_pos = self.__str_len + offset
            
            if final_str_pos < 0:
                raise ValueError("Negative position in stream.")
                
            self.__bytes_pos = self.__str_pos_to_bytes_pos(final_str_pos)
            self.__str_pos = final_str_pos
            self.__readable.value = self.__str_len - self.__str_pos
            return self.__str_pos
    
    def truncate(self, size: int | None = None):
        if size is None:
            size = self.__str_pos
        if not isinstance(size, int):
            raise TypeError(f"Expected int or None, got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            bytes_pos = self.__str_pos_to_bytes_pos(size)
            if len(self.__buffer) < bytes_pos:
                self.__buffer.extend(b"\0" * (bytes_pos - len(self.__buffer)))
            elif len(self.__buffer) > bytes_pos:
                self.__buffer = self.__buffer[:bytes_pos]
            self.__str_len = size
            self.__readable.value = self.__str_len - self.__str_pos

    def write(self, data: str) -> int:
        if not isinstance(data, str):
            raise TypeError(f"Expected str, got '{type(data).__name__}'")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            if self.__bytes_pos > len(self.__buffer):
                self.__buffer.extend(b"\0" * (self.__bytes_pos - len(self.__buffer)))
            str_start, str_end = self.__str_pos, self.__str_pos + len(data)             # String positions are the same by definition
            bytes_start, bytes_end = self.__bytes_pos, self.__str_pos_to_bytes_pos(str_end)     # But buffer position might differ depending on encoding leghts
            encoded_data = data.encode()

            if len(encoded_data) != bytes_end - bytes_start:        # Old and new substrings have different encoding lengths : move the end of the buffer
                moved_data = self.__buffer[bytes_end:]
                self.__buffer[bytes_start + len(encoded_data) : bytes_start + len(encoded_data) + len(moved_data)] = moved_data
                if len(encoded_data) < bytes_end - bytes_start:     # The new string is shorter : discard the old unerased end of the buffer
                    self.__buffer = self.__buffer[:bytes_start + len(encoded_data) + len(moved_data)]

            old_data = self.__buffer[bytes_start : bytes_end]
            self.__buffer[bytes_start : bytes_start + len(encoded_data)] = encoded_data
            self.__bytes_pos += len(encoded_data)
            self.__str_len -= len(old_data.decode())
            self.__str_len += len(data)
            self.__str_pos += len(data)
            self.__readable.value = self.__str_len - self.__str_pos
            return len(data)
    
    def read(self, size: int | float = float("inf")) -> str:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            bytes_start = self.__bytes_pos
            bytes_end = bytes_start
            for bytes_pos, str_pos in self.__parallel_walker(self.__bytes_pos):
                if str_pos == size:
                    bytes_end = bytes_start + bytes_pos
                    break
            else:
                bytes_end = len(self.__buffer)
            data = self.__buffer[bytes_start : bytes_end].decode()
            self.__bytes_pos = bytes_end
            self.__str_pos += len(data)
            self.__readable.value = self.__str_len - self.__str_pos
            return data
        
    def readinto(self, buffer: bytearray | memoryview, encoding : str = "utf-8") -> int:
        if not isinstance(buffer, bytearray | memoryview):
            raise TypeError(f"Expected writable buffer, got '{type(buffer).__name__}'")
        if not isinstance(encoding, str):
            raise TypeError(f"Expected str for encoding, got '{type(encoding).__name__}'")
        from codecs import lookup, getincrementalencoder
        try:
            lookup(encoding)
        except LookupError as e:
            raise e from None
        def reader():
            last_bytes_pos = -1
            for bytes_pos, str_pos in self.__parallel_walker(self.__bytes_pos):
                yield self.__buffer[last_bytes_pos + 1 : bytes_pos + 1].decode()
                last_bytes_pos = bytes_pos
        i = 0
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            writer = getincrementalencoder(encoding)()
            for char in reader():
                encoded_char = writer.encode(char)
                if i + len(encoded_char) >= len(buffer):
                    break
                buffer[i : i + len(encoded_char)] = encoded_char
                i += len(encoded_char)
                self.__str_pos += len(char)
            self.__readable.value = self.__str_len - self.__str_pos
        return i
    
    def readline(self, size: int | float = float("inf")) -> str:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        with self.lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            bytes_start = self.__bytes_pos
            bytes_end = bytes_start
            last_bytes_pos = -1
            for bytes_pos, str_pos in self.__parallel_walker(self.__bytes_pos):
                char = self.__buffer[self.__bytes_pos + last_bytes_pos + 1 : self.__bytes_pos + bytes_pos + 1].decode()
                if str_pos == size or char == "\n":
                    bytes_end = bytes_pos
                    break
                last_bytes_pos = bytes_pos
            else:
                bytes_end = len(self.__buffer)
            data = self.__buffer[bytes_start : bytes_end].decode()
            self.__bytes_pos = bytes_end
            self.__str_pos += len(data)
            self.__readable.value = self.__str_len - self.__str_pos
            return data
        




class BytesBuffer(AbstractBytesIO):

    """
    A subclass of Viper.abc.io.BytesIO that uses an internal buffer to act as a bytes stream.
    In contrast to BytesIO, they work like pipes:

    - Reading and writing are synchronized but can be done simultaneously.
    - They are not seekable.
    - Their internal buffer is circular and have a fixed size.
    - Closing first acts on the writing end : you will still be able to read the remaining data. Check the readable attribute to know if reading is still possible.
    """

    from .abc.io import IOClosedError as __IOClosedError

    __slots__ = {
        "__buffer" : "The internal buffer storing the stream.",
        "__start" : "The absolute position of the reading cursor in the stream.",
        "__end" : "The absolute position of the writing cursor in the stream.",
        "__closed" : "A boolean indicating if the stream has been closed.",
        "__readable" : "The readable Budget.",
        "__writable" : "The writable Budget."
    }

    def __init__(self, size : int = BUFFER_SIZE) -> None:
        if not isinstance(size, int):
            raise TypeError(f"Expected int, got '{type(size).__name__}'")
        if size <= 0:
            raise ValueError(f"Expected positive nonzero integer for buffer size, got {size}")
        from .abc.utils import Budget
        self.__buffer = bytearray(size)
        self.__start = 0
        self.__end = 0
        self.__readable = Budget()
        self.__writable = Budget(size)
        self.__closed : bool = False

    @property
    def readable(self):
        return self.__readable

    @property
    def writable(self):
        return self.__writable
        
    def fileno(self) -> int:
        raise OSError(f"{type(self).__name__} objects have no associated file descriptors")
    
    def close(self):
        self.__closed = True
        self.__writable.close()
        if not self.__readable:
            self.__readable.close()
        
    @property
    def closed(self) -> bool:
        return self.__closed
    
    def tell(self) -> int:
        if self.closed:
            from .abc.io import IOClosedError
            raise IOClosedError(f"{type(self).__name__} is closed")
        return self.__end
    
    def seekable(self) -> bool:
        return False
    
    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        raise OSError(f"{type(self).__name__} is not seekable")
    
    def truncate(self, size: int | None = None):
        raise OSError(f"{type(self).__name__} is not truncable")
    
    def write(self, data: bytes | bytearray | memoryview) -> int:
        if not isinstance(data, bytes | bytearray | memoryview):
            raise TypeError(f"Expected readable buffer, got '{type(data).__name__}'")
        data = memoryview(data)
        done = 0
        with self.write_lock:
            if self.closed and not self.__writable:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            while done < len(data):

                with self.__writable as available:

                    if not available:
                        break

                    next_packet = data[done : min(len(data), done + available)]

                    if self.__start % len(self.__buffer) > self.__end % len(self.__buffer):     # Writing in the middle of the buffer
                        self.__buffer[self.__end % len(self.__buffer) : (self.__end % len(self.__buffer)) + len(next_packet)] = next_packet

                    else:                                                                       # Writing up to the end of the buffer
                        breakpoint = (-self.__end) % len(self.__buffer)     # How much space remains from __end to the end of the buffer
                        if breakpoint == 0:                                 # Special case when __end = __start = 0
                            breakpoint = len(self.__buffer)
                        packet1, packet2 = next_packet[:breakpoint], next_packet[breakpoint:]
                        self.__buffer[self.__end % len(self.__buffer) : self.__end % len(self.__buffer) + len(packet1)] = packet1
                        self.__buffer[0 : len(packet2)] = packet2
                    
                    self.__end += len(next_packet)
                    self.__readable += len(next_packet)
                    self.__writable -= len(next_packet)
                    done += len(next_packet)

            return done
    
    def read(self, size: int | float = float("inf")) -> bytes:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        if not isinstance(size, float):
            buffer = bytearray(size)
        else:
            buffer = bytearray()
        read = 0
        with self.read_lock:
            if self.closed and not self.__readable:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            while read < size:

                with self.__readable as available:

                    if not available:
                        break
                    
                    if self.__start % len(self.__buffer) < self.__end % len(self.__buffer):     # Reading in the middle of the buffer
                        packet = memoryview(self.__buffer)[self.__start % len(self.__buffer) : self.__end % len(self.__buffer)]
                        packet = packet[:min(len(packet), size - read)]
                    
                    else:                                                                       # Reading up to the end of the buffer
                        packet = memoryview(b"" + memoryview(self.__buffer)[self.__start % len(self.__buffer) :] + memoryview(self.__buffer)[: self.__end % len(self.__buffer)])
                        packet = packet[:min(len(packet), size - read)]

                    buffer[read : read + len(packet)] = packet
                    
                    self.__start += len(packet)
                    read += len(packet)
                    try:
                        self.__writable += len(packet)
                    except RuntimeError:
                        pass
                    self.__readable -= len(packet)

            if self.closed and self.__readable == 0 and not self.__readable.closed:
                self.__readable.close()
            
            return bytes(memoryview(buffer)[:read])
    
    def readinto(self, buffer: bytearray | memoryview) -> int:
        if not isinstance(buffer, bytearray | memoryview):
            raise TypeError(f"Expected writable buffer, got '{type(buffer).__name__}'")
        size = len(buffer)
        read = 0
        with self.read_lock:
            if self.closed and not self.__readable:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            while read < size:

                with self.__readable as available:

                    if not available:
                        break
                    
                    if self.__start % len(self.__buffer) < self.__end % len(self.__buffer):     # Reading in the middle of the buffer
                        packet = memoryview(self.__buffer)[self.__start % len(self.__buffer) : self.__end % len(self.__buffer)]
                        packet = packet[:min(len(packet), size - read)]
                    
                    else:                                                                       # Reading up to the end of the buffer
                        packet = memoryview(b"" + memoryview(self.__buffer)[self.__start % len(self.__buffer) :] + memoryview(self.__buffer)[: self.__end % len(self.__buffer)])
                        packet = packet[:min(len(packet), size - read)]

                    buffer[read : read + len(packet)] = packet
                    
                    self.__start += len(packet)
                    read += len(packet)
                    try:
                        self.__writable += len(packet)
                    except RuntimeError:
                        pass
                    self.__readable -= len(packet)

            if self.closed and self.__readable == 0 and not self.__readable.closed:
                self.__readable.close()

            return read
    
    def readline(self, size: int | float = float("inf")) -> bytes:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        if not isinstance(size, float):
            buffer = bytearray(size)
        else:
            buffer = bytearray()
        read = 0
        with self.read_lock:
            if self.closed and not self.__readable:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            while read < size:

                with self.__readable as available:

                    if not available:
                        break

                    if self.__start % len(self.__buffer) < self.__end % len(self.__buffer):     # Reading in the middle of the buffer
                        packet = memoryview(self.__buffer)[self.__start % len(self.__buffer) : self.__end % len(self.__buffer)]
                        packet = packet[:min(len(packet), size - read)]
                    
                    else:                                                                       # Reading up to the end of the buffer
                        packet = memoryview(b"" + memoryview(self.__buffer)[self.__start % len(self.__buffer) :] + memoryview(self.__buffer)[: self.__end % len(self.__buffer)])
                        packet = packet[:min(len(packet), size - read)]

                    packet = packet.tobytes()
                    if b"\n" in packet:
                        packet = packet[:packet.index(b"\n") + 1]
                    buffer[read : read + len(packet)] = packet
                    
                    self.__start += len(packet)
                    read += len(packet)
                    try:
                        self.__writable += len(packet)
                    except RuntimeError:
                        pass
                    self.__readable -= len(packet)

                    if packet.endswith(b"\n"):
                        break
            
            if self.closed and self.__readable == 0 and not self.__readable.closed:
                self.__readable.close()

            return bytes(memoryview(buffer)[:read])
        




class StringBuffer(AbstractStringIO):

    """
    A subclass of Viper.abc.io.StringIO that uses an internal buffer to act as a string stream.
    In contrast to StringIO, they work like pipes:

    - Reading and writing are synchronized but can be done simultaneously.
    - They are not seekable.
    - Their internal buffer is circular and have a fixed size. Small additional space may be allocated for complex encodings.
    - Closing first acts on the writing end : you will still be able to read the remaining data. Check the readable attribute to know if reading is still possible.
    """

    from .abc.io import IOClosedError as __IOClosedError

    __slots__ = {
        "__buffer" : "The internal buffer storing the stream.",
        "__start" : "The absolute position of the reading cursor in the stream.",
        "__end" : "The absolute position of the writing cursor in the stream.",
        "__extra" : "A buffer that will store some extra data that could not fit in the stream due to larger encodings.",
        "__closed" : "A boolean indicating if the stream has been closed.",
        "__readable" : "The readable Budget.",
        "__writable" : "The writable Budget.",
        "__total" : "The total amount of characters written in the Unicode domain."
    }
    
    @staticmethod
    def __incremental_chunck_decoder(maxsize : int | float, stop_at_newline : bool) -> Generator[tuple[int, str], bytes, None]:
        """
        Internal generator that decodes strings from sent chunks of data.
        Yields the number of bytes used from each input and the new decoded character(s).
        Given the maxsize, it ensures not to decode more characters than needed.
        """
        from codecs import getincrementaldecoder
        decoder = getincrementaldecoder("utf-8")()
        chars : str | list[str]
        decoded_chars = 0
        running = True
        data = yield (0, "")

        while running:
            init_state = decoder.getstate()
            chars = decoder.decode(data)
            used = len(data)

            if stop_at_newline and "\n" in chars:       # We need to find how many bytes were necessary to decode the newline
                running = False
                if chars.index("\n") != len(chars) - 1: # newline is not the last character. We cannot skip the search for the minimum data.
                    decoder.setstate(init_state)
                    chars = []
                    used = 0
                    for j in range(len(data)):
                        byte = data[j : j + 1]
                        char = decoder.decode(byte)
                        chars.append(char)
                        used += 1
                        if char == "\n":
                            break
                    chars = "".join(chars)

            if decoded_chars + len(chars) > maxsize:    # We have decoded more than necessary. Got again incrementally.
                decoder.setstate(init_state)
                missing = maxsize - decoded_chars
                size = 0
                chars = []
                used = 0
                for j in range(len(data)):
                    byte = data[j : j + 1]
                    char = decoder.decode(byte)
                    chars.append(char)
                    size += len(char)
                    used += 1
                    if size >= missing:
                        break
                chars = "".join(chars)

            decoded_chars += len(chars)            
            data = yield used, chars

            if decoded_chars >= maxsize:
                running = False

    def __init__(self, size : int = BUFFER_SIZE) -> None:
        if not isinstance(size, int):
            raise TypeError(f"Expected int, got '{type(size).__name__}'")
        if size <= 0:
            raise ValueError(f"Expected positive nonzero integer for buffer size, got {size}")
        from .abc.utils import Budget
        self.__buffer = bytearray(size)
        self.__extra = b""
        self.__start = 0
        self.__end = 0
        self.__readable = Budget()
        self.__writable = Budget(size)
        self.__closed : bool = False
        self.__total = 0
    
    @property
    def readable(self):
        return self.__readable

    @property
    def writable(self):  # This is an approximation, but if the approximation fails, self.__extra will store the data that can't be stored in the buffer
        return self.__writable
        
    def fileno(self) -> int:
        raise OSError(f"{type(self).__name__} objects have no associated file descriptors")
    
    def close(self):
        self.__closed = True
        self.__writable.close()
        if not self.__readable:
            self.__readable.close()
        
    @property
    def closed(self) -> bool:
        return self.__closed
    
    def tell(self) -> int:
        if self.closed:
            raise self.__IOClosedError(f"{type(self).__name__} is closed")
        return self.__total
    
    def seekable(self) -> bool:
        return False
    
    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        raise OSError(f"{type(self).__name__} is not seekable")
    
    def truncate(self, size: int | None = None):
        raise OSError(f"{type(self).__name__} is not truncable")
        
    def write(self, data: str) -> int:
        if not isinstance(data, str):
            raise TypeError(f"Expected str, got '{type(data).__name__}'")
        from codecs import getincrementalencoder
        encoder = getincrementalencoder("utf-8")()
        done = 0
        with self.write_lock:
            if self.closed:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            while done < len(data):

                with self.__writable as available:

                    if not available:
                        break

                    bavailable = ((self.__start - self.__end) % len(self.__buffer)) if self.__start != self.__end else len(self.__buffer)

                    done += len(spacket := data[done : done + available])
                    packet = self.__extra + encoder.encode(spacket)
                    packet, extra = memoryview(packet)[:bavailable], packet[available:]

                    if self.__start % len(self.__buffer) > self.__end % len(self.__buffer):     # Writing in the middle of the buffer
                        self.__buffer[self.__end % len(self.__buffer) : self.__end % len(self.__buffer) + len(packet)] = packet

                    else:                                                                       # Writing up to the end of the buffer
                        breakpoint = (-self.__end) % len(self.__buffer)     # How much space remains from __end to the end of the buffer
                        if breakpoint == 0:                                 # Special case when __end = __start = 0
                            breakpoint = len(self.__buffer)
                        packet1, packet2 = packet[:breakpoint], packet[breakpoint:]
                        self.__buffer[self.__end % len(self.__buffer) : self.__end % len(self.__buffer) + len(packet1)] = packet1
                        self.__buffer[0 : len(packet2)] = packet2

                    self.__end += len(packet)
                    self.__extra = extra
                    self.__readable += len(spacket)
                    self.__writable -= len(spacket)
            
            self.__total += done

            return done
        
    def __write_extra(self):
        """
        Internal function used to write extra data without blocking.
        There might still be some extra data after calling it: it will write as much as possible within the remaining space.
        """
        with self.write_lock:
            available = ((self.__start - self.__end) % len(self.__buffer)) if self.__start != self.__end else len(self.__buffer)
            bdata, self.__extra = self.__extra[:available], self.__extra[available:]
            if bdata:
                if self.__start % len(self.__buffer) > self.__end % len(self.__buffer):     # Writing in the middle: do it in one step
                    self.__buffer[self.__end % len(self.__buffer) : self.__end % len(self.__buffer) + len(bdata)] = bdata
                else:
                    br = (-self.__end) % len(self.__buffer)
                    if br == 0:     # Special case : everyone is at zero % bufsize
                        br = len(self.__buffer)
                    bdata1 = bdata[:br]
                    bdata2 = bdata[br:]
                    self.__buffer[self.__end % len(self.__buffer) : self.__end % len(self.__buffer) + len(bdata1)] = bdata1
                    self.__buffer[:len(bdata2)] = bdata2
                self.__end += len(bdata)
    
    def read(self, size: int | float = float("inf")) -> str:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        read = 0
        with self.read_lock:
            if self.closed and self.__start == self.__end:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            read_generator = self.__incremental_chunck_decoder(size, False)
            next(read_generator)

            data_blocks : list[str] = []
            
            while read < size:

                with self.__readable as available:

                    if not available:
                        break

                    if self.__end - self.__start == 0 and self.__extra:
                        self.__write_extra()
                    
                    if self.__start % len(self.__buffer) < self.__end % len(self.__buffer):     # Reading in the middle of the buffer
                        packet = memoryview(self.__buffer)[self.__start % len(self.__buffer) : self.__end % len(self.__buffer)]
                    
                    else:                                                                       # Reading up to the end of the buffer
                        packet = memoryview(b"" + memoryview(self.__buffer)[self.__start % len(self.__buffer) :] + memoryview(self.__buffer)[: self.__end % len(self.__buffer)])

                    if len(packet) > size - read:
                        packet = packet[:size - read]

                    used_bytes, chars = read_generator.send(bytes(packet))
                    data_blocks.append(chars)
                    packet = packet[:used_bytes]

                    self.__start += len(packet)
                    read += len(chars)
                    try:
                        self.__writable += len(chars)
                    except RuntimeError:
                        pass
                    self.__readable -= len(chars)
            
            return "".join(data_blocks)
        
    def readline(self, size: int | float = float("inf")) -> str:
        if not isinstance(size, int) and size != float("inf"):
            raise TypeError(f"Expected int of float('inf'), got '{type(size).__name__}'")
        if size < 0:
            raise ValueError(f"Expected positive integer, got {size}")
        read = 0
        with self.read_lock:
            if self.closed and self.__start == self.__end:
                raise self.__IOClosedError(f"{type(self).__name__} is closed")
            
            read_generator = self.__incremental_chunck_decoder(size, True)
            next(read_generator)

            data_blocks : list[str] = []
            
            while read < size:

                with self.__readable as available:

                    if not available:
                        break

                    if self.__end - self.__start == 0 and self.__extra:
                        self.__write_extra()
                    
                    if self.__start % len(self.__buffer) < self.__end % len(self.__buffer):     # Reading in the middle of the buffer
                        packet = memoryview(self.__buffer)[self.__start % len(self.__buffer) : self.__end % len(self.__buffer)]
                    
                    else:                                                                       # Reading up to the end of the buffer
                        packet = memoryview(b"" + memoryview(self.__buffer)[self.__start % len(self.__buffer) :] + memoryview(self.__buffer)[: self.__end % len(self.__buffer)])

                    if len(packet) > size - read:
                        packet = packet[:size - read]

                    used_bytes, chars = read_generator.send(bytes(packet))
                    data_blocks.append(chars)
                    packet = packet[:used_bytes]

                    self.__start += len(packet)
                    read += len(chars)
                    try:
                        self.__writable += len(chars)
                    except RuntimeError:
                        pass
                    self.__readable -= len(chars)

                    if chars.endswith("\n"):
                        break
            
            return "".join(data_blocks)
    

                


del SEEK_SET, RLock, Generator, Iterator, AbstractBytesIO, AbstractStringIO