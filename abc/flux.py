"""
This module defines a flux operator.
"""

from abc import abstractmethod
from typing import Optional
from Viper.abc.io import BytesReader, BytesWriter

__all__ = ["FluxOperator"]





class FluxOperator:

    """
    FluxOperators should handle a BytesReader and a BytesWriter, apply a flux operation from the input stream and write the result on the output stream.
    If the class attribute "inverse" is not None, it should be another subclass of FluxOperator that performs the inverse operation.
    """

    inverse : Optional["FluxOperator"] = None

    def __init__(self, source : BytesReader, destination : BytesWriter) -> None:
        from .io import BytesReader, BytesWriter
        if not isinstance(source, BytesReader) or not isinstance(destination, BytesWriter):
            raise TypeError("Expected BytesReader and BytesWriter, got " + repr(type(source).__name__) + " and " + repr(type(destination).__name__))
        
        self.__source = source
        self.__destination = destination

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
    
    @abstractmethod
    def run(self):
        """
        This method should perform the flux operation until the input stream is closed.
        if the output stream closes first, it should raise RuntimeError.
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