from proj_types.webmethod import WebMethod
from web.handler import WebHandler
from web.response import WebResponse


class OptionsHandler(WebHandler):
    def can_handle(self) -> bool:
        if self._request.method is None:
            return False

        return self._request.method == WebMethod.OPTIONS

    def handle(self, response: WebResponse) -> None:
        response.code = 204
        response.msg = "No Content"

        response.headers["Allow"] = ", ".join(
            [
                e.value
                for n, e in WebMethod._member_map_.items()
                if not n.startswith("_")
            ]
        )
        response.headers["DAV"] = "1"
