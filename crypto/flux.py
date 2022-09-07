"""
This module adds multiple flux operator for cryptographic purposes.
"""

from Viper.abc.flux import FluxOperator
from Viper.abc.io import BytesReader, BytesWriter

__all__ = ["AESCTREncryptorOperator", "AESCTRDecryptorOperator", "AuthenticatedEncryptorOperator", "AuthenticatedDecryptorOperator", "EncryptorOperator", "DecryptorOperator"]

PACKET_SIZE = 2 ** 15





class AESCTREncryptorOperator(FluxOperator):

    """
    This flux operator will encrypt the input flux into the destination flux using the AES block cipher with CTR mode.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview, *, auto_close: bool = False) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if not isinstance(key, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(key).__name__))
        if len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        from os import urandom
        from threading import RLock
        self.__key = bytes(key)
        self.__nonce = urandom(16)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
    
    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = bytes(value)
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for encrypting this stream.
        """
        return self.__nonce
    
    @nonce.setter
    def nonce(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) != 16:
            raise ValueError("Expected a 128-bits nonce.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change nonce while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change nonce once encryption is finished.")
            self.__nonce = bytes(value)

    def run(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        with self.__parameter_lock:
            self.__running = True
        cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).encryptor()
        from pickle import dumps
        from Viper.abc.io import IOClosedError
        bnonce = dumps(self.__nonce)
        try:
            self.destination.write(bnonce)
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        while True:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(cipher.update(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(cipher.finalize())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
        self.__running = False
        if self.auto_close:
            self.destination.close()
    
    @property
    def finished(self) -> bool:
        return self.__done



class AESCTRDecryptorOperator(FluxOperator):

    """
    This flux operator will decrypt the input flux into the destination flux using the AES block cipher with CTR mode.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview, *, auto_close: bool = False) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if not isinstance(key, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(key).__name__))
        if len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        from threading import RLock
        self.__key = bytes(key)
        self.__nonce = b""
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
    
    @property
    def key(self) -> bytes:
        """
        The key used for decryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = bytes(value)
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for decrypting this stream. Becomes available once decryption has started.
        """
        return self.__nonce
    
    def run(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        with self.__parameter_lock:
            self.__running = True
        from Viper.pickle_utils import safe_load
        from Viper.abc.io import IOClosedError
        try:
            self.__nonce = safe_load(self.source)
        except IOClosedError as e:
            raise RuntimeError("The source stream got closed before the operator could initialize decryption") from e
        if not isinstance(self.__nonce, bytes) or len(self.__nonce) != 16:
            raise RuntimeError("The input stream does not match the interface of AESCTREncryptorOperator.")
        cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).decryptor()
        while True:
            try:
                packet = self.source.read(PACKET_SIZE)
            except IOClosedError:
                break
            try:
                self.destination.write(cipher.update(packet))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        try:
            self.destination.write(cipher.finalize())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
        self.__running = False
        if self.auto_close:
            self.destination.close()
    
    @property
    def finished(self) -> bool:
        return self.__done


AESCTREncryptorOperator.inverse = AESCTRDecryptorOperator
AESCTRDecryptorOperator.inverse = AESCTREncryptorOperator




class AuthenticatedEncryptorOperator(FluxOperator):

    """
    This flux operator will encrypt the input flux into the destination flux using the AES block cipher with CTR mode and adds integrity checksums before encryption.
    Combined, these two properties ensure the authenticity of the decrypted message.
    Raises AuthenticationError when the decrypted message was not encrypted with the given cipher key.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview, *, auto_close: bool = False) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if not isinstance(key, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(key).__name__))
        if len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        from os import urandom
        from threading import RLock
        self.__key = bytes(key)
        self.__nonce = urandom(16)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
    
    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = bytes(value)
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for encrypting this stream.
        """
        return self.__nonce
    
    @nonce.setter
    def nonce(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) != 16:
            raise ValueError("Expected a 128-bits nonce.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change nonce while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change nonce once encryption is finished.")
            self.__nonce = bytes(value)

    def run(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        with self.__parameter_lock:
            self.__running = True
        cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).encryptor()
        from pickle import dump
        from Viper.abc.io import IOClosedError
        size = PACKET_SIZE
        try:
            dump(self.__nonce, self.destination)
            self.destination.write(cipher.update(size.to_bytes(8, "little")))
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        from hmac import digest
        while True:
            try:
                packet = self.source.read(size)
            except IOClosedError:
                break
            checksum = digest(self.key, packet, "SHA512")
            try:
                self.destination.write(cipher.update(packet))
                self.destination.write(cipher.update(checksum))
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
            if len(packet) < size:
                break
        try:
            self.destination.write(cipher.finalize())
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
        self.__running = False
        if self.auto_close:
            self.destination.close()
    
    @property
    def finished(self) -> bool:
        return self.__done




class AuthenticatedDecryptorOperator(FluxOperator):

    """
    This flux operator will decrypt the input flux into the destination flux using the AES block cipher with CTR mode and checks integrity checksums regularly.
    Raises AuthenticationError when the decrypted message was not encrypted with the given cipher key.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview, *, auto_close: bool = False) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if not isinstance(key, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(key).__name__))
        if len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        from threading import RLock
        self.__key = bytes(key)
        self.__nonce = b""
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
    
    @property
    def key(self) -> bytes:
        """
        The key used for decryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview):
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError("Expected readable buffer for key, got " + repr(type(value).__name__))
        if len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = bytes(value)
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for decrypting this stream. Becomes available once decryption has started.
        """
        return self.__nonce
    
    def run(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        with self.__parameter_lock:
            self.__running = True
        from Viper.pickle_utils import safe_load, ForbiddenPickleError
        from Viper.abc.io import IOClosedError
        try:
            self.__nonce = safe_load(self.source)
            if not isinstance(self.__nonce, bytes):
                raise ForbiddenPickleError("Expected bytes, got " + repr(type(self.__nonce).__name__))
        except ForbiddenPickleError as e:
            from .exceptions import AuthenticationError
            raise AuthenticationError("The source stream was altered and contained unexpected objects.") from e
        except IOClosedError as e:
            raise RuntimeError("The source stream got closed before the operator could initialize decryption") from e
        if not isinstance(self.__nonce, bytes) or len(self.__nonce) != 16:
            raise RuntimeError("The input stream does not match the interface of AESCTREncryptorOperator.")
        cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).decryptor()
        from hmac import digest, compare_digest
        packet = b""
        while len(packet) < 8:
            try:
                packet += cipher.update(self.source.read(8))
            except IOClosedError as e:
                raise RuntimeError("The source stream got closed before the operator could initialize decryption") from e
        size = int.from_bytes(packet[:8], "little")
        packet = packet[8:]
        running = True
        while running:
            while len(packet) < size + 64:
                try:
                    packet += cipher.update(self.source.read(size + 64))
                except IOClosedError:
                    packet += cipher.finalize()
                    running = False
                    break
            if not packet:
                break
            if len(packet) >= size + 64:
                block, received_checksum, packet = packet[:size], packet[size : size + 64], packet[size + 64:]
            else:
                block, received_checksum, packet = packet[:-64], packet[-64:], b""
            computed_checksum = digest(self.key, block, "SHA512")
            if not compare_digest(received_checksum, computed_checksum):
                from .exceptions import AuthenticationError
                raise AuthenticationError("The source message has either been corrupted or modified by an attacker.")
            try:
                self.destination.write(block)
            except IOClosedError as e:
                raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
        self.__done = True
        self.__running = False
        if self.auto_close:
            self.destination.close()
    
    @property
    def finished(self) -> bool:
        return self.__done


AuthenticatedEncryptorOperator.inverse = AuthenticatedDecryptorOperator
AuthenticatedDecryptorOperator.inverse = AuthenticatedEncryptorOperator

EncryptorOperator = AuthenticatedEncryptorOperator
DecryptorOperator = AuthenticatedDecryptorOperator




del FluxOperator, BytesReader, BytesWriter