import mimetypes
import os
import constants
from web.handler import WebHandler
from web.response import WebResponse


class StaticHandler(WebHandler):
    STATIC_PREFIX = "/s/"

    def can_handle(self) -> bool:
        path = self._request.path
        if path is None:
            return False

        return path.startswith(self.STATIC_PREFIX)

    def handle(self, response: WebResponse) -> None:
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
            response.code = 400
            response.msg = "No"
            return

        if not os.path.isfile(path):
            response.code = 404
            response.msg = "Not found"
            return

        # Read the requested file
        with open(path, "rb") as rf:
            response.body = rf.read()

        # Guess the MIME type of the file
        response.headers["Content-Type"] = (
            mimetypes.guess_type(path)[0] or "application/octet-stream"
        )

        # Tell the browser static pages can be cached
        response.headers["Cache-Control"] = "public, max-age=604800"
