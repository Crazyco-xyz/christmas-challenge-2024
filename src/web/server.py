import select
import socket
import threading
import time
from typing import Type

from log import LOG
from proj_types.proto_error import ProtocolError
from web.handler import WebHandler
from web.request import WebRequest


class WebServer:
    def __init__(
        self,
        port: int,
        proto_handler: Type[WebRequest],
        request_handlers: list[Type[WebHandler]],
        hostname: str = "0.0.0.0",
    ) -> None:
        self._port: int = port

        # The handler for reading in the protocol
        self._proto_handler: Type[WebRequest] = proto_handler

        # The handler for actually providing content
        self._request_handlers: list[Type[WebHandler]] = request_handlers
        self._hostname: str = hostname

        # Create the socket used for receiving requests
        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Fix for linux blocking the port after exit
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._hostname, self._port))

    def start_background(self) -> None:
        """Starts the `start_blocking` method in a separate Thread"""

        threading.Thread(
            target=self.start_blocking,
            daemon=True,
            name=f"WebServer@{self._port}",
        ).start()

    def start_blocking(self) -> None:
        """Starts the WebServer using the provided protocol and port"""

        LOG.info(f"Starting server on 0.0.0.0:{self._port}")

        # Listen to the socket until getting ^C
        try:
            self._socket.listen()
            self._listen()
        except KeyboardInterrupt:
            LOG.info("Registered ^C, exiting...")

        # Close the server socket upon closing
        self._socket.close()

    def _listen(self) -> None:
        """Listens to the socket for requests and passes them to `_handle` for handling"""

        while True:
            try:
                readable, _, _ = select.select([self._socket], [], [], 0)
                if self._socket not in readable:
                    time.sleep(0.1)
                    continue

                sock, addr = self._socket.accept()

                threading.Thread(
                    target=self._handle,
                    args=(sock, addr),
                    name="RequestHandler",
                    daemon=True,
                ).start()

            except Exception:
                LOG.debug(
                    "Exception encountered while receiving data from socket:",
                    exc_info=True,
                )

    def _handle(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        """Handles the request using the provided protocol

        Args:
            sock (socket.socket): The accepted socket awaiting handling
            addr (tuple[str, int]): The address of the socket
        """

        try:
            LOG.debug("Received request from %s", str(addr))

            # Read the request using the protocol handler
            request = self._proto_handler(sock, addr)
            request.handle()

            # Check for the first request handler able to handle this request
            for handler_type in self._request_handlers:
                handler = handler_type(request)
                if not handler.can_handle():
                    continue

                # Create response and handle request
                response = request.response()
                handler.handle(response)

                # Send the response modified by the request handler and return
                LOG.info(
                    "%s: %d [%s] for %s by %s",
                    handler.__class__.__name__,
                    response.code,
                    response.msg,
                    request.path,
                    addr[0],
                )
                response.send()
                return

            # No handler found, send error
            response = request.response()
            response.code = 404
            response.msg = "Not Found"

            response.send()

        except ProtocolError:
            LOG.exception("Could not handle request because of protocol related error!")
        except Exception:
            LOG.exception("Unhandled exception while handling request!")
        finally:
            # Close the socket if not closed yet
            sock.close()
