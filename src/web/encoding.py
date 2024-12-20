import abc
import gzip
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
    def name(self) -> str:
        """
        Returns:
            str: The name of the encoding algorithm
        """

        pass

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

    def name(self) -> str:
        """
        Returns:
            str: The name of the encoding algorithm
        """

        return "deflate"
