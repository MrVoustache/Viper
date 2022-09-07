"""
This module defines a flux operator.
"""

from abc import abstractmethod
from typing import Any, Optional, Type
from Viper.abc.io import BytesReader, BytesWriter

__all__ = ["FluxOperator"]





class FluxOperator:

    """
    FluxOperators should handle a BytesReader and a BytesWriter, apply a flux operation from the input stream and write the result on the output stream.
    If the class attribute "inverse" is not None, it should be another subclass of FluxOperator that performs the inverse operation.
    If auto_close is True, then, when run() has finished its work, it should close the destination stream.
    """

    inverse : Optional["FluxOperator"] = None

    def __init__(self, source : BytesReader, destination : BytesWriter, *, auto_close : bool = False) -> None:
        from .io import BytesReader, BytesWriter
        if not isinstance(source, BytesReader) or not isinstance(destination, BytesWriter):
            raise TypeError("Expected BytesReader and BytesWriter, got " + repr(type(source).__name__) + " and " + repr(type(destination).__name__))
        if not isinstance(auto_close, bool):
            raise TypeError("Expected bool for auto_close, got " + repr(type(auto_close).__name__))

        self.__source = source
        self.__destination = destination
        self.__auto_close = auto_close
    
    @staticmethod
    def get_init_args() -> tuple[tuple, dict[str, Any]] | Type[NotImplemented]:
        """
        Called by a class that wants to create a FluxOperator instance if they don't know the parameters other than source and destination.
        It should return a tuple of positional args and a dictionary of keyword args.
        It should ask the user if necessary (example : ask a passphrase for a cryptographic flux).
        Returns NotImplemented if the subclass does not require additional arguments.
        Raise NotImplementedError() if supplying those arguments is not possible.
        """
        return NotImplemented

    @property
    def source(self) -> BytesReader:
        """
        The input stream of the flux operator.
        """
        return self.__source
    
    @property
    def destination(self) -> BytesWriter:
        """
        The output stream of the flux operator.
        """
        return self.__destination
    
    @property
    def auto_close(self) -> bool:
        """
        If auto_close is True, the destination stream will be closed when the work of run() is finished.
        """
        return self.__auto_close
    
    @abstractmethod
    def run(self):
        """
        This method should perform the flux operation until the input stream is closed.
        If the output stream closes first, it should raise RuntimeError.
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def finished(self) -> bool:
        """
        True if the stream operation is finished, i.e. if the input stream has been closed and the last operation has been written to the output stream.
        """
        raise NotImplementedError()   



del abstractmethod, Optional, BytesReader, BytesWriter