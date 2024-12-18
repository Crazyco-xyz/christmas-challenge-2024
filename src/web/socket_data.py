from io import BufferedReader, BufferedWriter
import io
import os
import socket

from log import LOG


class DataReceiver:
    CHUNK_LENGTH = 4096

    def __init__(self, sock: socket.socket, recv_length: int) -> None:
        self._sock: socket.socket = sock
        self._recv_length: int = 0
        self._recv_length = recv_length

    def receive_into(self, filehandle: BufferedWriter | io.BytesIO) -> None:
        while self._recv_length > 0:
            # Read the data chunk from the socket
            chunk = self._sock.recv(min(self.CHUNK_LENGTH, self._recv_length))
            self._recv_length -= len(chunk)

            # Write the chunk to file
            filehandle.write(chunk)
            filehandle.flush()

        filehandle.close()


class DataSender:
    CHUNK_LENGTH = 4096

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._file = open(file_path, "rb")

    def send_to(self, sock: socket.socket) -> None:
        while chunk := self._file.read(self.CHUNK_LENGTH):
            sent = 0
            while sent < len(chunk):
                sent += sock.send(chunk[sent:])

        self._file.close()

    def __len__(self) -> int:
        return os.path.getsize(self._file_path)
