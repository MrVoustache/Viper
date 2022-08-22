"""
This module describes simpler interfaces for connection objects.
These are closer to the Connection objects from the multiprocessing package than sockets.
"""

from abc import ABCMeta, abstractmethod
from typing import AsyncIterator, Iterator, Optional





class BufferTooSmall(Exception):

    """
    This exception means that the given buffer was not big enough to complete an operation it was provided for.
    """



class ConnectionClosedError(ConnectionError):

    """
    This exception is raised when an operation is attempted on a closed connection object.
    """




class Address(metaclass = ABCMeta):

    """
    This class describes the minimum requirements for address objects.
    """

    @abstractmethod
    def __reduce__(self) -> str | tuple:
        raise NotImplementedError()

    def __str__(self) -> str:
        return type(self).__name__ + " object pointing at " + str(self.to_int())
    
    def to_int(self) -> int:
        """
        Returns an integer that represents the address. Call Address.from_int() on the result to get back the same address.
        """
        from random import randbytes
        from pickle import dumps
        return int.from_bytes(randbytes(1) + dumps(self) + randbytes(1), "little")

    @classmethod
    def from_int(i : int, /) -> "Address":
        """
        Returns the address associated to the given interger. Get such an integer by calling add.to_int() on an Address object.
        """
        from pickle import loads
        return loads(i.to_bytes((i.bit_length() + 7) // 8, "little")[1:-1])





class ConnectionBase(metaclass = ABCMeta):

    """
    This class describes basic methods required for most types of connections.
    """

    @abstractmethod
    def fileno(self) -> int:
        """
        If available, returns the file descriptor (integer) representing the underlying connection for the system.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def close(self):
        """
        Closes the connection.
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def closed(self) -> bool:
        """
        Returns True if the connection has already been closed
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def local_address(self) -> Address:
        """
        Returns the local address of the connection (the Address object that the other side would get by calling remote_address on their Connection object).
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def remote_address(self) -> Address:
        """
        Returns the address that the object is connected to.
        """
        raise NotImplementedError()
    
    def __del__(self):
        """
        Implements destruction of self.
        """
        self.close()
    



class Sender(ConnectionBase):
    
    """
    This class describes an interface for a sender connection.
    """

    @abstractmethod
    def send(self, data : bytes | bytearray | memoryview, offset : int = 0, size : Optional[int] = None, /):
        """
        Sends all of data to the other side of the connection. Blocks if necessary.
        If given, will start sending the message from offset instead of the beginning of the buffer.
        If given, will send at most size bytes (sends all bytes available otherwise).
        Raises ConnectionError of failure.
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def asend(self, data : bytes | bytearray | memoryview, offset : int = 0, size : Optional[int] = None, /):
        """
        Asynchronous version of send.
        """
        raise NotImplementedError()




class Receiver(ConnectionBase):

    """
    This class describes an interface for a receiver connection.
    """

    @abstractmethod
    def recv(self) -> bytes:
        """
        Receives a message of bytes from the other side. Blocks until the next message arrives.
        The size of the message is the size of the buffer passed to send() by the other side.
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def arecv(self) -> bytes:
        """
        Asynchronous version of recv.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def recv_into(self, buffer : bytearray | memoryview, offset : int = 0, /) -> int:
        """
        Receives the next message in the given buffer and returns the size of the message.
        If given, will only start writing at offset position in the buffer.
        If the buffer doesn't have enough space to write the message, raises BufferTooSmall. An empty bytearray can also be given, and will be allocated with the corresponding size.
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def arecv_into(self, buffer : bytearray | memoryview, offset : int = 0, /) -> int:
        """
        Asynchronous version of recv_into.
        """

    def __iter__(self) -> Iterator[bytes]:
        """
        Iterates over all the messages received.
        """
        while not self.closed:
            yield self.recv()
    
    async def __aiter__(self) -> AsyncIterator[bytes]:
        """
        Asynchronously iterates over all the messages received.
        """
        while not self.closed:
            yield await self.arecv()




class Connection(Sender, Receiver):

    """
    This class describes the interface of a bidirectional connection.
    """



del ABCMeta, abstractmethod, Optional, Iterator, AsyncIterator