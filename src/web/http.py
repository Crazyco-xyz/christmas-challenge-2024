import socket
import constants
from log import LOG
from proj_types.proto_error import ProtocolError
from proj_types.webmethod import WebMethod
from web.request import WebRequest
from web.response import WebResponse


class HttpRequest(WebRequest):
    def __init__(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        super().__init__(sock, addr)

    def _read_line(self) -> str:
        """Reads one line from the request socket

        Returns:
            str: The line read, not including any padding like `\r\n`
        """

        buffer: list[bytes] = []

        # Read data into buffer until encountering `\n`
        while (c := self._socket.recv(1)) != b"\n":
            buffer.append(c)

        # Joining and stripping the buffer
        return b"".join(buffer).decode().strip()

    def handle(self) -> None:
        """Read in the request"""

        self._read_status()
        self._read_headers()
        self._read_body()

    def _read_status(self) -> None:
        """Reads the status line and parses it into their corresponding variables

        Raises:
            ProtocolError: Upon encountering any protocol related error
        """

        # Read status
        status = self._read_line().split(" ", 2)

        # Check for 3 status arguments
        if len(status) != 3:
            raise ProtocolError(f"The status line {str(status)} needs three arguments!")

        # Check for the appropriate HTTP version
        if status[2].upper() != constants.HTTP_VERSION:
            raise ProtocolError(f"Unknown version {status[2]} could not be recognized!")

        # Parse status into variables
        self._method = WebMethod(status[0])
        self._path = status[1]

    def _read_headers(self) -> None:
        """Read all provided headers

        Raises:
            ProtocolError: Upon encountering any protocol related error
        """

        while True:
            # Read header line
            l = self._read_line()

            # Check if end of headers is reached (empty line)
            if len(l) == 0:
                return

            # Split header into key and value
            header = l.split(": ", 1)
            if len(header) != 2:
                raise ProtocolError("The header must have a key and value!")

            # Store header into CaseInsensitiveDict
            self._headers[header[0]] = header[1]

    def _read_body(self) -> None:
        """Read the body if the request has one

        Raises:
            ProtocolError: Upon encountering any protocol related error
        """

        # Check if there is a body
        if "Content-Length" not in self._headers:
            return

        # Get the length of the body
        try:
            content_length = int(self._headers["Content-Length"])
        except ValueError as e:
            raise ProtocolError("Content-Length must be a number!", e)

        # Receive the body
        self._body = self._socket.recv(content_length)

    def response(self) -> WebResponse:
        """
        Returns:
            WebResponse: The HTTP response based on this request
        """

        return HttpResponse(self._socket)


class HttpResponse(WebResponse):
    def __init__(self, sock: socket.socket) -> None:
        super().__init__(sock)

    def _send_line(self, line: str) -> None:
        """Sends the specified line plus line terminators `\r\n`

        Args:
            line (str): The line to be sent
        """

        self._socket.sendall(line.encode() + b"\r\n")

    def send(self) -> None:
        """Sends the response to the requesting socket"""

        # Append `Content-Length` if necessary
        if self.body is not None:
            self.headers["Content-Length"] = str(len(self.body))

        self._send_status()
        self._send_headers()
        self._send_body()

        self._socket.close()

    def _send_status(self) -> None:
        """Sends the status line"""

        self._send_line(f"{constants.HTTP_VERSION} {self.code} {self.msg}")

    def _send_headers(self) -> None:
        """Sends all headers plus the empty line denoting the end of headers"""

        for key, val in self.headers.items():
            self._send_line(f"{key}: {val}")

        self._send_line("")

    def _send_body(self) -> None:
        """Sends the response body if specified"""

        if self.body is None:
            return

        self._socket.sendall(self.body)
