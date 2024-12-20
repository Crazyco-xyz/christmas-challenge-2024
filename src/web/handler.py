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
        """
        Returns:
            bool: Whether this handler can handle the request
        """

        pass

    @abc.abstractmethod
    def handle(self, response: WebResponse) -> None:
        """Handle the request and populate the response object

        Args:
            response (WebResponse): The response object to populate
        """

        pass

    def get_session(self) -> Optional[Session]:
        """Get the session for the current request

        Returns:
            Optional[Session]: The session object if it exists
        """

        # Get the cookie header from the request
        cookie_header = self._request.headers.get("Cookie", "")

        # If there is no cookie header, return None
        if len(cookie_header) == 0:
            return None

        cookies: dict[str, str] = {}

        # Parse the cookie header into a dictionary
        for cookie in cookie_header.split("; "):
            if "=" not in cookie:
                continue

            cookie_parts = cookie.split("=")
            cookies[cookie_parts[0]] = cookie_parts[1]

        # Get the session from the session storage
        return SessionStorage().get_session(
            self._request.ip, cookies.get("session", "")
        )


class ErrorHandler(WebHandler):
    def can_handle(self) -> bool:
        """
        Returns:
            bool: Whether this handler can handle the request
        """

        return True

    def handle(self, response: WebResponse) -> None:
        """The fallback error handler for when no other handler can handle the request

        Args:
            response (WebResponse): The response object to populate
        """

        response.code, response.msg = 404, "Not Found"
        response.body = b"This page could not be found!"
