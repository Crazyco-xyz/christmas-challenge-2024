from io import BufferedWriter
import socket

from log import LOG


class DataReceiver:
    CHUNK_LENGTH = 4096

    def __init__(self, sock: socket.socket, recv_length: int) -> None:
        self._sock: socket.socket = sock
        self._recv_length: int = 0
        self._recv_length = recv_length

    def receive_into(self, filehandle: BufferedWriter) -> None:
        while self._recv_length > 0:
            # Read the data chunk from the socket
            chunk = self._sock.recv(min(self.CHUNK_LENGTH, self._recv_length))
            self._recv_length -= len(chunk)

            # Write the chunk to file
            filehandle.write(chunk)
            filehandle.flush()
