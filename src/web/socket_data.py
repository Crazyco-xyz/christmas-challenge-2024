from io import BufferedWriter
import io
import os
import socket
from typing import Callable

import constants

type Compressor = Callable[[bytes], bytes]


class DataReceiver:
    def __init__(self, sock: socket.socket, recv_length: int) -> None:
        self._sock: socket.socket = sock
        self._recv_length: int = 0
        self._recv_length: int = recv_length
        self._decompression: list[Compressor] = []

    def receive_into(self, filehandle: BufferedWriter | io.BytesIO) -> None:
        """Receives data from the socket and writes it to the filehandle

        Args:
            filehandle (BufferedWriter | io.BytesIO): The filehandle to write the data to
        """

        while self._recv_length > 0:
            # Read the data chunk from the socket
            chunk = self._sock.recv(
                min(constants.BUFFERED_CHUNK_SIZE, self._recv_length)
            )

            # Subtract the length of the chunk from the total length
            self._recv_length -= len(chunk)

            for c in self._decompression:
                chunk = c(chunk)

            # Write the chunk to file
            filehandle.write(chunk)
            filehandle.flush()

        filehandle.close()

    def decompress(self, decompressor: Compressor) -> None:
        self._decompression.append(decompressor)


class DataSender:
    def __init__(self, file_path: str) -> None:
        self._file_path: str = file_path
        self._compression: list[Compressor] = []

    def send_to(self, sock: socket.socket) -> None:
        """Sends the file to the socket

        Args:
            sock (socket.socket): The socket to send the file to
        """

        # Open the file in read-binary mode
        file = open(self._file_path, "rb")

        # While the file has content to read
        while len(chunk := file.read(constants.BUFFERED_CHUNK_SIZE)) > 0:

            for c in self._compression:
                chunk = c(chunk)

            # Send the data read from the file to the socket
            sent = 0
            while sent < len(chunk):
                sent += sock.send(chunk[sent:])

        file.close()

    def compress(self, compressor: Compressor) -> None:
        self._compression.append(compressor)

    def __len__(self) -> int:
        """
        Returns:
            int: The size of the file in bytes
        """

        return os.path.getsize(self._file_path)
