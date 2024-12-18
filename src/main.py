import os
import constants
from log import LOG
from web.api_handler import APIHandler
from web.handler import ErrorHandler
from web.http import HttpRequest
from web.interface_handler import InterfaceHandler
from web.options_handler import OptionsHandler
from web.server import WebServer

from web.static_handler import StaticHandler
from webdav.webdav_handler import WebDavHandler

if __name__ != "__main__":
    LOG.warning("This file should not be imported! Try executing it directly.")
    exit(1)

# Create the files dir, because it wont get cloned using GIT
os.makedirs(constants.FILES, exist_ok=True)


# The stack of handlers to use
handler_stack = [
    OptionsHandler,
    WebDavHandler,
    APIHandler,
    StaticHandler,
    InterfaceHandler,
    ErrorHandler,
]

# HTTP server
WebServer(
    constants.HTTP_PORT,
    HttpRequest,
    handler_stack,
).start_background()

# HTTPS server
WebServer(
    constants.HTTPS_PORT,
    HttpRequest,
    handler_stack,
    use_tls=True,
).start_blocking()
