"""
This module defines FluxOperators for multiple compression and decompression algorithms.
"""

from Viper.abc.flux import FluxOperator
from Viper.abc.io import BytesReader, BytesWriter

__all__ = ["BZ2CompressorOperator", "BZ2DecompressorOperator", "LZMACompressorOperator", "LZMADecompressorOperator", "SnappyCompressorOperator", "SnappyDecompressorOperator"]

PACKET_SIZE = 2 ** 15





class BZ2CompressorOperator(FluxOperator):

    """
    Performs the compression of input stream into output stream with the bzip2 algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from bz2 import BZ2Compressor
        from Viper.abc.io import IOClosedError
        compressor = BZ2Compressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(compressor.compress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(compressor.flush())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done




class BZ2DecompressorOperator(FluxOperator):

    """
    Performs the decompression of input stream into output stream with the bzip2 algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from bz2 import BZ2Decompressor
        from Viper.abc.io import IOClosedError
        decompressor = BZ2Decompressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(decompressor.decompress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done


BZ2CompressorOperator.inverse = BZ2DecompressorOperator
BZ2DecompressorOperator.inverse = BZ2CompressorOperator




class LZMACompressorOperator(FluxOperator):

    """
    Performs the compression of input stream into output stream with the lzma algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from lzma import LZMACompressor
        from Viper.abc.io import IOClosedError
        compressor = LZMACompressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(compressor.compress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(compressor.flush())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done




class LZMADecompressorOperator(FluxOperator):

    """
    Performs the decompression of input stream into output stream with the lzma algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from lzma import LZMADecompressor
        from Viper.abc.io import IOClosedError
        decompressor = LZMADecompressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(decompressor.decompress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done


LZMACompressorOperator.inverse = LZMADecompressorOperator
LZMADecompressorOperator.inverse = LZMACompressorOperator




class SnappyCompressorOperator(FluxOperator):

    """
    Performs the compression of input stream into output stream with Google's snappy algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from snappy import StreamCompressor
        from Viper.abc.io import IOClosedError
        compressor = StreamCompressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(compressor.compress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(compressor.flush())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done




class SnappyDecompressorOperator(FluxOperator):

    """
    Performs the decompression of input stream into output stream with Google's snappy algorithm.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter) -> None:
        super().__init__(source, destination)
        self.__done = False

    def run(self):
        from snappy import StreamDecompressor
        from Viper.abc.io import IOClosedError
        decompressor = StreamDecompressor()
        while not self.source.closed:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(decompressor.decompress(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(decompressor.flush())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
    
    @property
    def finished(self) -> bool:
        return self.__done


SnappyCompressorOperator.inverse = SnappyDecompressorOperator
SnappyDecompressorOperator.inverse = SnappyCompressorOperator



del FluxOperator, BytesReader, BytesWriter