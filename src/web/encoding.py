import abc
import gzip
import zlib


class Encoding(abc.ABC):
    @abc.abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass

    @abc.abstractmethod
    def name(self) -> str:
        pass

    @staticmethod
    def supported_encodings() -> "list[Encoding]":
        return [
            Gzip(),
            Deflate(),
        ]


class Gzip(Encoding):
    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data)

    def name(self) -> str:
        return "gzip"


class Deflate(Encoding):
    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    def name(self) -> str:
        return "deflate"
