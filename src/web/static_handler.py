import mimetypes
import os
import constants
from web.handler import WebHandler
from web.response import WebResponse
from web.socket_data import DataSender


class StaticHandler(WebHandler):
    STATIC_PREFIX = "/s/"

    def can_handle(self) -> bool:
        """
        Returns:
            bool: Whether this handler can handle the request
        """

        path = self._request.path
        if path is None:
            return False

        return path.startswith(self.STATIC_PREFIX)

    def handle(self, response: WebResponse) -> None:
        """Handle the request

        Args:
            response (WebResponse): The response to send static files to
        """

        file_path = self._request.path
        if file_path is None:
            return

        # Strip the /s/ from the path
        file_path = file_path[len(self.STATIC_PREFIX) :]
        static_path = os.path.abspath(os.path.join(constants.WEB, "static"))

        # Join the static path and the requested path
        path = os.path.join(static_path, file_path)

        # The user tried to access a file outside of the static directory
        if os.path.commonpath([static_path]) != os.path.commonpath([static_path, path]):
            response.code, response.msg = 400, "Nope"
            return

        if not os.path.isfile(path):
            response.code, response.msg = 404, "Not found"
            return

        # Send the requested file
        response.body = DataSender(path)

        # Guess the MIME type of the file
        response.headers["Content-Type"] = (
            mimetypes.guess_type(path)[0] or constants.MIME_FALLBACK
        )

        # Tell the browser static pages can be cached
        response.headers["Cache-Control"] = "public, max-age=604800"
