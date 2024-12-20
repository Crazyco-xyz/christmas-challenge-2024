import abc
import gzip
from typing import Callable, Optional
import zlib


class Encoding(abc.ABC):
    @abc.abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compresses the given data using the encoding algorithm

        Args:
            data (bytes): The data to compress

        Returns:
            bytes: The compressed data
        """

        pass

    @abc.abstractmethod
    def chunked_compression(self) -> Optional[Callable[[bytes], bytes]]:
        """
        Returns:
            Optional[Callable[[bytes], bytes]]: A compressor for chunked compression
        """

        pass

    @abc.abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompresses the given data using the encoding algorithm

        Args:
            data (bytes): The data to decompress

        Returns:
            bytes: The decompressed data
        """

        pass

    @abc.abstractmethod
    def chunked_decompression(self) -> Optional[Callable[[bytes], bytes]]:
        """
        Returns:
            Optional[Callable[[bytes], bytes]]: A decompressor for chunked decompression
        """

        pass

    @abc.abstractmethod
    def name(self) -> str:
        """
        Returns:
            str: The name of the encoding algorithm
        """

        pass

    @staticmethod
    def get_encoding(name: str) -> "Optional[Encoding]":
        """Retrieves the encoding algorithm by name

        Args:
            name (str): The name of the encoding algorithm

        Returns:
            Optional[Encoding]: The encoding algorithm or `None` if it doesn't exist
        """

        for encoding in Encoding.supported_encodings():
            if encoding.name() == name:
                return encoding

        return None

    @staticmethod
    def supported_encodings() -> "list[Encoding]":
        """
        Returns:
            list[Encoding]: A list of supported encoding algorithms
        """

        return [
            Gzip(),
            Deflate(),
        ]


class Gzip(Encoding):
    def compress(self, data: bytes) -> bytes:
        """Compresses the given data using the encoding algorithm

        Args:
            data (bytes): The data to compress

        Returns:
            bytes: The compressed data
        """

        return gzip.compress(data)

    def chunked_compression(self) -> Optional[Callable[[bytes], bytes]]:
        return None

    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)

    def chunked_decompression(self) -> Optional[Callable[[bytes], bytes]]:
        return None

    def name(self) -> str:
        """
        Returns:
            str: The name of the encoding algorithm
        """

        return "gzip"


class Deflate(Encoding):
    def compress(self, data: bytes) -> bytes:
        """Compresses the given data using the encoding algorithm

        Args:
            data (bytes): The data to compress

        Returns:
            bytes: The compressed data
        """

        return zlib.compress(data)

    def chunked_compression(self) -> Callable[[bytes], bytes]:
        compress_obj = zlib.compressobj(level=9)

        def compress(data: bytes) -> bytes:
            return compress_obj.compress(data) + compress_obj.flush(zlib.Z_SYNC_FLUSH)

        return compress

    def decompress(self, data: bytes) -> bytes:
        return zlib.decompress(data)

    def chunked_decompression(self) -> Callable[[bytes], bytes]:
        decompress_obj = zlib.decompressobj()

        def decompress(data: bytes) -> bytes:
            return decompress_obj.decompress(data)

        return decompress

    def name(self) -> str:
        """
        Returns:
            str: The name of the encoding algorithm
        """

        return "deflate"
