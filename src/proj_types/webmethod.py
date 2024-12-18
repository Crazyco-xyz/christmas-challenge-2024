from enum import Enum


class WebMethod(Enum):
    GET = "GET"
    POST = "POST"
    OPTIONS = "OPTIONS"

    # WebDAV methods
    PROPFIND = "PROPFIND"
    MKCOL = "MKCOL"
    DELETE = "DELETE"
    PUT = "PUT"
    COPY = "COPY"
    PROPPATCH = "PROPPATCH"
    MOVE = "MOVE"
