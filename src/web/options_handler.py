from proj_types.webmethod import WebMethod
from web.encoding import Encoding
from web.handler import WebHandler
from web.response import WebResponse


class OptionsHandler(WebHandler):
    def can_handle(self) -> bool:
        """
        Returns:
            bool: Whether this handler can handle the request
        """

        if self._request.method is None:
            return False

        return self._request.method == WebMethod.OPTIONS

    def handle(self, response: WebResponse) -> None:
        """Send the OPTIONS response to the client

        Args:
            response (WebResponse): The response to this request
        """

        response.code, response.msg = 204, "No Content"

        # Set the Allow and DAV headers
        response.headers["Allow"] = ", ".join(
            [
                e.value
                for n, e in WebMethod._member_map_.items()
                if not n.startswith("_")
            ]
        )
        response.headers["DAV"] = "1, 3"
        response.headers["Accept-Encoding"] = "deflate"
