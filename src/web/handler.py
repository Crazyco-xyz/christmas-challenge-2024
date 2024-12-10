import abc
from typing import Optional
from web.request import WebRequest
from web.response import WebResponse
from web.session import Session, SessionStorage


class WebHandler(abc.ABC):
    def __init__(self, request: WebRequest) -> None:
        self._request: WebRequest = request

    @abc.abstractmethod
    def can_handle(self) -> bool:
        pass

    @abc.abstractmethod
    def handle(self, response: WebResponse) -> None:
        pass

    def get_session(self) -> Optional[Session]:
        cookie_header = self._request.headers.get("Cookie", "")

        if len(cookie_header) == 0:
            return None

        cookies: dict[str, str] = {}

        for cookie in cookie_header.split("; "):
            if "=" not in cookie:
                continue

            cookie_parts = cookie.split("=")
            cookies[cookie_parts[0]] = cookie_parts[1]

        return SessionStorage().get_session(
            self._request.ip, cookies.get("session", "")
        )


class ErrorHandler(WebHandler):
    def can_handle(self) -> bool:
        return True

    def handle(self, response: WebResponse) -> None:
        response.code = 404
        response.msg = "Not Found"
        response.body = b"This page could not be found!"
