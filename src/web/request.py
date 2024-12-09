import abc
import socket
from typing import Optional, Type

from proj_types.case_insensitive_dict import CaseInsensitiveDict
from proj_types.webmethod import WebMethod
from web.response import WebResponse


class WebRequest(abc.ABC):
    def __init__(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        self._socket: socket.socket = sock
        self._addr: tuple[str, int] = addr

        self._path: Optional[str] = None
        self._method: Optional[WebMethod] = None
        self._headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
        self._body: Optional[bytes] = None

    @property
    def path(self) -> Optional[str]:
        """The requested path

        Returns:
            Optional[str]: The path or `None` if it hasn't been read yet
        """

        return self._path

    @property
    def method(self) -> Optional[WebMethod]:
        """The requested method

        Returns:
            Optional[WebMethod]: The method or `None` if it hasn't been read yet
        """

        return self._method

    @property
    def headers(self) -> CaseInsensitiveDict[str]:
        """The request headers

        Returns:
            CaseInsensitiveDict[str]: The headers sent by the client
        """

        return self._headers

    @property
    def body(self) -> Optional[bytes]:
        """The request body

        Returns:
            Optional[bytes]: The body or `None` if it hasn't been read yet
        """

        return self._body

    @property
    def ip(self) -> str:
        """The IP this request originates from

        Returns:
            str: The IP address
        """

        return self._addr[0]

    @abc.abstractmethod
    def handle(self) -> None:
        """Abstract method for reading in the request"""

        pass

    @abc.abstractmethod
    def response(self) -> WebResponse:
        """Abstract method for creating the response

        Returns:
            WebResponse: The response implemented with the protocol which received the request
        """

        pass
