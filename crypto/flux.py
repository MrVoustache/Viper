"""
This module adds multiple flux operator for cryptographic purposes.
"""

from typing import Any
from Viper.abc.flux import FluxOperator
from Viper.abc.io import BytesReader, BytesWriter
from .session import SecuritySession

__all__ = ["AESCTREncryptorOperator", "AESCTRDecryptorOperator", "AuthenticatedEncryptorOperator", "AuthenticatedDecryptorOperator", "EncryptorOperator", "DecryptorOperator"]

PACKET_SIZE = 2 ** 15

_sessions : dict[tuple[str], SecuritySession] = {}

def _module_stacktrace() -> tuple[str]:
            from inspect import stack
            s = []
            for info in stack():
                name = info.filename
                if not s or s[-1] != name:
                    s.append(name)
            return tuple(s)





class AESCTREncryptorOperator(FluxOperator):

    """
    This flux operator will encrypt the input flux into the destination flux using the AES block cipher with CTR mode.
    """

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview | str | None = None, *, auto_close: bool = False, reuse_passphrase : bool = True) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if key != None and not isinstance(key, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(key).__name__))
        if key != None and not isinstance(key, str) and len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if not isinstance(reuse_passphrase, bool):
            raise TypeError("Expected bool for reuse_passphrase, got " + repr(type(reuse_passphrase).__name__))
        from os import urandom
        from threading import RLock
        self.__nonce = urandom(16)
        self.__key = key
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
        self.__reuse_passphrase = reuse_passphrase
        self.__initialized = False
    
    def initialize(self):

        if self.__initialized:
            return
        self.__initialized = True

        with self.__parameter_lock:
            self.__running = True

        if self.__key == None and self.__reuse_passphrase:
            ident = _module_stacktrace()
            try:
                self.__key = next(iter(_sessions[ident]))
            except:
                pass

        if self.__key == None:
            from .utils import ask_user_passphrase_twice
            self.__key = ask_user_passphrase_twice("Enter passphrase for encryption > ")
        
        ident = _module_stacktrace()
        if self.__reuse_passphrase and (ident not in _sessions or len(list(_sessions[ident])) == 0):
            if ident not in _sessions:
                from .session import SecuritySession
                _sessions[ident] = SecuritySession()
            session = _sessions[ident]
            session.add(self.__key)

        if isinstance(self.__key, str):
            from .utils import derive_passphrase
            self.__key = derive_passphrase(self.__key, salt = self.__nonce)

    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview | str):
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(value).__name__))
        if not isinstance(value, str) and len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = value
    
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
        self.initialize()
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
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

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview | str | None = None, *, auto_close: bool = False, reuse_passphrase : bool = True) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if key != None and not isinstance(key, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(key).__name__))
        if key != None and not isinstance(key, str) and len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if not isinstance(reuse_passphrase, bool):
            raise TypeError("Expected bool for reuse_passphrase, got " + repr(type(reuse_passphrase).__name__))
        from os import urandom
        from threading import RLock
        self.__nonce = urandom(16)
        self.__key = key
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
        self.__initialized = False
        self.__reuse_passphrase = reuse_passphrase
    
    def initialize(self):

        if self.__initialized:
            return
        self.__initialized = True

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

        if self.__key == None:
            from .utils import ask_user_passphrase
            self.__key = ask_user_passphrase("Enter passphrase for decryption > ")
        
        ident = _module_stacktrace()
        if self.__reuse_passphrase and (ident not in _sessions or len(list(_sessions[ident])) == 0):
            if ident not in _sessions:
                from .session import SecuritySession
                _sessions[ident] = SecuritySession()
            session = _sessions[ident]
            session.add(self.__key)

        if isinstance(self.__key, str):
            from .utils import derive_passphrase
            self.__key = derive_passphrase(self.__key, salt = self.__nonce)

    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview | str):
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(value).__name__))
        if not isinstance(value, str) and len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = value
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for decrypting this stream. Becomes available once decryption has started.
        """
        return self.__nonce
    
    def run(self):
        self.initialize()
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from Viper.abc.io import IOClosedError
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

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview | str | None = None, *, auto_close: bool = False, reuse_passphrase : bool = True) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if key != None and not isinstance(key, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(key).__name__))
        if key != None and not isinstance(key, str) and len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if not isinstance(reuse_passphrase, bool):
            raise TypeError("Expected bool for reuse_passphrase, got " + repr(type(reuse_passphrase).__name__))
        from os import urandom
        from threading import RLock
        self.__nonce = urandom(16)
        self.__key = key
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
        self.__reuse_passphrase = reuse_passphrase
        self.__initialized = False
    
    def initialize(self):

        if self.__initialized:
            return
        self.__initialized = True

        with self.__parameter_lock:
            self.__running = True

        if self.__key == None and self.__reuse_passphrase:
            ident = _module_stacktrace()
            try:
                self.__key = next(iter(_sessions[ident]))
            except:
                pass

        if self.__key == None:
            from .utils import ask_user_passphrase_twice
            self.__key = ask_user_passphrase_twice("Enter passphrase for encryption > ")

        ident = _module_stacktrace()
        if self.__reuse_passphrase:
            if ident not in _sessions:
                from .session import SecuritySession
                _sessions[ident] = SecuritySession()
            session = _sessions[ident]
            session.add(self.__key)

        if isinstance(self.__key, str):
            from .utils import derive_passphrase
            self.__key = derive_passphrase(self.__key, salt = self.__nonce)

    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview | str):
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(value).__name__))
        if not isinstance(value, str) and len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = value
    
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
        self.initialize()
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).encryptor()
        from pickle import dump
        from hmac import digest
        from Viper.abc.io import IOClosedError
        size = PACKET_SIZE
        try:
            dump(self.__nonce, self.destination)
            self.destination.write(cipher.update(digest(self.__key, self.__nonce, "SHA512")))
            self.destination.write(cipher.update(size.to_bytes(8, "little")))
        except IOClosedError as e:
            raise RuntimeError("The destination stream got closed before the operator could finish writing its output") from e
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

    def __init__(self, source: BytesReader, destination: BytesWriter, key : bytes | bytearray | memoryview | str | None = None, *, auto_close: bool = False, reuse_passphrase : bool = True) -> None:
        super().__init__(source, destination, auto_close=auto_close)
        if key != None and not isinstance(key, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(key).__name__))
        if key != None and not isinstance(key, str) and len(key) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if not isinstance(reuse_passphrase, bool):
            raise TypeError("Expected bool for reuse_passphrase, got " + repr(type(reuse_passphrase).__name__))
        from os import urandom
        from threading import RLock
        self.__nonce = urandom(16)
        self.__key = key
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        self.__running = False
        self.__done = False
        self.__parameter_lock = RLock()
        self.__reuse_passphrase = reuse_passphrase
        self.__initialized = False
    
    def initialize(self):

        if self.__initialized:
            return
        self.__initialized = True

        with self.__parameter_lock:
            self.__running = True
                
        self.__packet = b""

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

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from .utils import derive_passphrase
        from hmac import digest, compare_digest 

        while len(self.__packet) < 64:
            try:
                self.__packet += self.source.read(64)
            except IOClosedError as e:
                raise RuntimeError("The source stream got closed before the operator could initialize decryption") from e
        key_check = self.__packet[:64]

        if self.__key == None and self.__reuse_passphrase:
            ident = _module_stacktrace()
            if ident in _sessions:
                session = _sessions[ident]
                for key in session:
                    if isinstance(key, str):
                        key = derive_passphrase(key, salt = self.__nonce)
                    self.__cipher = Cipher(algorithms.AES(key), modes.CTR(self.__nonce)).decryptor()
                    decrypted_key_check = self.__cipher.update(key_check)[:64]
                    if len(decrypted_key_check) != 64:
                        raise RuntimeError("It did not work...")
                    if compare_digest(decrypted_key_check, digest(key, self.__nonce, "SHA512")):
                        self.__key = key

        ok = False
        max_attempts = 3
        attempts = 1

        while not ok:

            old_key = self.__key

            if self.__key == None:
                from .utils import ask_user_passphrase
                self.__key = ask_user_passphrase("Enter passphrase for decryption > " if attempts <= 1 else "Wrong passphrase, try again > ")
                ident = _module_stacktrace()
                if self.__reuse_passphrase:
                    if ident not in _sessions:
                        from .session import SecuritySession
                        _sessions[ident] = SecuritySession()
                    session = _sessions[ident]
                    session.add(self.__key)

            if isinstance(self.__key, str):
                from .utils import derive_passphrase
                self.__key = derive_passphrase(self.__key, salt = self.__nonce)
            
            self.__cipher = Cipher(algorithms.AES(self.__key), modes.CTR(self.__nonce)).decryptor()
            decrypted_key_check = self.__cipher.update(key_check[:64])
            self.__packet = self.__packet[64:]
            if len(decrypted_key_check) != 64:
                raise RuntimeError("It did not work...")
            ok = compare_digest(decrypted_key_check, digest(self.__key, self.__nonce, "SHA512"))
            if not ok and attempts >= max_attempts:
                from .exceptions import InvalidKeyError
                raise InvalidKeyError("The given decryption key does not match the encryption key that was used to encrypt this stream.")
            elif not ok:
                attempts += 1
                self.__key = old_key

    @property
    def key(self) -> bytes:
        """
        The key used for encryption. Can be 128, 192 or 256 bits long.
        """
        return self.__key
    
    @key.setter
    def key(self, value : bytes | bytearray | memoryview | str):
        if not isinstance(value, bytes | bytearray | memoryview | str):
            raise TypeError("Expected readable buffer or str for key, got " + repr(type(value).__name__))
        if not isinstance(value, str) and len(value) not in (16, 24, 32):
            raise ValueError("Expected a 128, 192 or 256 bits key.")
        if isinstance(self.__key, bytearray | memoryview):
            self.__key = bytes(self.__key)
        with self.__parameter_lock:
            if self.__running:
                raise RuntimeError("Cannot change cipher key while encrypting a message.")
            if self.__done:
                from Viper.abc.io import IOClosedError
                raise IOClosedError("Cannot change key once encryption is finished.")
            self.__key = value
    
    @property
    def nonce(self) -> bytes:
        """
        A random value used for decrypting this stream. Becomes available once decryption has started.
        """
        return self.__nonce
    
    def run(self):
        self.initialize()

        from Viper.abc.io import IOClosedError
        from hmac import digest, compare_digest
        
        while len(self.__packet) < 8:
            try:
                self.__packet += self.__cipher.update(self.source.read(8))
            except IOClosedError as e:
                raise RuntimeError("The source stream got closed before the operator could initialize decryption") from e
        size = int.from_bytes(self.__packet[:8], "little")
        self.__packet = self.__packet[8:]

        running = True
        while running:
            while len(self.__packet) < size + 64:
                try:
                    self.__packet += self.__cipher.update(self.source.read(size + 64))
                except IOClosedError:
                    self.__packet += self.__cipher.finalize()
                    running = False
                    break
            if not self.__packet:
                break
            if len(self.__packet) >= size + 64:
                block, received_checksum, self.__packet = self.__packet[:size], self.__packet[size : size + 64], self.__packet[size + 64:]
            else:
                block, received_checksum, self.__packet = self.__packet[:-64], self.__packet[-64:], b""
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