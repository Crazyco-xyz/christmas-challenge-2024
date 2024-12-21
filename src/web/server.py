import os
import select
import socket
import ssl
import threading
import time
from typing import Type

import constants
from log import LOG
from proj_types.proto_error import ProtocolError
from proj_types.webmethod import WebMethod
from web.handler import WebHandler
from web.request import WebRequest


class WebServer:
    def __init__(
        self,
        port: int,
        proto_handler: Type[WebRequest],
        request_handlers: list[Type[WebHandler]],
        hostname: str = "0.0.0.0",
        use_tls: bool = False,
    ) -> None:
        self._port: int = port

        # The handler for reading in the protocol
        self._proto_handler: Type[WebRequest] = proto_handler

        # The handler for actually providing content
        self._request_handlers: list[Type[WebHandler]] = request_handlers
        self._hostname: str = hostname

        # Create the socket used for receiving requests
        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if use_tls:
            self._setup_tls()

        # Fix for linux blocking the port after exit
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._hostname, self._port))

    def _setup_tls(self) -> None:
        """Wraps the socket inside a TLS wrapper

        Raises:
            FileNotFoundError: When the key or certificate could not be found
        """

        # Paths to the certificate and key
        cert_path = os.path.join(constants.ROOT, "cert.pem")
        key_path = os.path.join(constants.ROOT, "key.pem")

        # Check if the certificate and key exist
        if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
            raise FileNotFoundError(
                "The key or certificate file for TLS could not be found."
            )

        # Create an SSL context and load the cert/key
        context = ssl.SSLContext()
        context.load_cert_chain(
            certfile=cert_path,
            keyfile=key_path,
        )

        # Wrap the socket inside the context
        self._socket = context.wrap_socket(self._socket, server_side=True)

    def start_background(self) -> None:
        """Starts the `start_blocking` method in a separate Thread"""

        threading.Thread(
            target=self.start_blocking,
            daemon=True,
            name="WebServer",
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
                # Check if the socket is readable
                readable, _, _ = select.select([self._socket], [], [], 0)
                if self._socket not in readable:
                    # Sleep for a bit to prevent 100% CPU usage
                    time.sleep(0.1)
                    continue

                # Accept the incoming connection
                sock, addr = self._socket.accept()

                # Handle the request in a separate thread
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

                LOG.info(
                    "%s: %d [%s] for %s: %s by %s",
                    handler.__class__.__name__,
                    response.code,
                    response.msg,
                    (request.method or WebMethod.GET).value,
                    request.path,
                    addr[0],
                )

                # Send the response modified by the request handler and return
                response.send()
                return

            # No handler found, send error
            response = request.response()
            response.code, response.msg = 500, "No Handler Found"

            response.send()

        except ProtocolError as e:
            LOG.warning(
                "Could not handle request because of protocol related error: %s", e.desc
            )
        except Exception:
            LOG.exception("Unhandled exception while handling request!")
        finally:
            # Close the socket if not closed yet
            sock.close()
