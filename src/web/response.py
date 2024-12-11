import abc
import json
import socket
from typing import Any, Optional

from proj_types.case_insensitive_dict import CaseInsensitiveDict


class WebResponse(abc.ABC):
    def __init__(
        self,
        sock: socket.socket,
        recv_headers: CaseInsensitiveDict[str],
    ) -> None:
        self._socket: socket.socket = sock
        self._recv_headers: CaseInsensitiveDict[str] = recv_headers

        self._code: int = 200
        self._msg: str = "OK"
        self._headers: dict[str, str] = {}
        self._body: Optional[bytes] = None

    @property
    def code(self) -> int:
        """
        Returns:
            int: The status code for the response
        """

        return self._code

    @code.setter
    def code(self, val: int) -> None:
        """
        Args:
            val (int): The new status code for the response
        """

        self._code = val

    @property
    def msg(self) -> str:
        """
        Returns:
            str: The message sent along the status code
        """

        return self._msg

    @msg.setter
    def msg(self, val: str) -> None:
        """
        Args:
            val (str): The new message to be sent
        """

        self._msg = val

    @property
    def headers(self) -> dict[str, str]:
        """
        Returns:
            dict[str, str]: The headers sent with the response
        """

        return self._headers

    @property
    def body(self) -> Optional[bytes]:
        """
        Returns:
            Optional[bytes]: The body for the response
        """

        return self._body

    @body.setter
    def body(self, val: bytes) -> None:
        """
        Args:
            val (bytes): The new body to be sent

        Note:
            The `Content-Length` header gets set automatically upon sending
        """

        self._body = val

    def json_body(self, json_data: dict[str, Any]) -> None:
        self._body = json.dumps(json_data).encode()

    @abc.abstractmethod
    def send(self) -> None:
        """Sends the response back to the original requester"""

        pass
