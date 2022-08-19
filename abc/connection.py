"""
This module describes simpler interfaces for connection objects.
These are closer to the Connection objects from the multiprocessing package than sockets.
"""

from abc import ABCMeta, abstractmethod
from typing import Optional





class BufferTooSmall(Exception):

    """
    This exception means that the given buffer was not big enough to complete an operation it was provided for.
    """




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
    



class Sender(ConnectionBase):
    
    """
    This class describes an interface for a sender connection.
    """

    @abstractmethod
    def send(self, data : bytes | bytearray | memoryview, offset : int = 0, size : Optional[int] = None, /):
        """
        Sends all of data to the other side of the connection. Blocks if necessary.
        If given, will start sending data from offset instead of the beginning of the buffer.
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
        Receives a packet of bytes from the other side. Blocks until the next packet arrives.
        The size of the packet is the size of the buffer passed to send() by the other side.
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def arecv(self) -> bytes:
        """
        Asynchronous version of recv.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def recv_into(buffer : bytearray | memoryview, offset : int = 0) -> int:
        """
        Receives the next packet in the given buffer and returns the size of the packet.
        If given, will only start writing at offset position in the buffer.
        If the buffer doesn't have enough space to write the message, raises BufferTooSmall. An empty bytearray can also be given, and will be allocated with the corresponding size.
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def arecv_into(buffer : bytearray | memoryview, offset : int = 0) -> int:
        """
        Asynchronous version of recv_into.
        """




class Connection(Sender, Receiver):

    """
    This class describes the interface of a bidirectional connection.
    """