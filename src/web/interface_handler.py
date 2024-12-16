import os
import constants
from web.handler import WebHandler
from web.response import WebResponse
from web.session import Session, SessionStorage


class InterfaceHandler(WebHandler):
    def can_handle(self) -> bool:
        if self._request.path == None:
            return False

        if self._request.path == "/":
            return True

        paths = ["~", "login", "register", "preview", "share", "logout"]
        for p in paths:
            if self._request.path.startswith(f"/{p}"):
                return True

        return False

    def handle(self, response: WebResponse) -> None:
        if self._request.path == None:
            return

        path = self._request.path.split("/")
        if len(path[0]) == 0:
            path.pop(0)

        # Check if the user is logged in
        if (session := self.get_session()) is None:
            self._no_session(path, response)

        else:
            self._session(session, path, response)

    def _no_session(self, path: list[str], response: WebResponse) -> None:
        """Sends the pages the user can request without login

        Args:
            path (list[str]): The path the user requested
            response (WebResponse): The response to send the file to
        """

        if path[0] == "login":
            self.send_file("login.html", response)

        elif path[0] == "register":
            self.send_file("register.html", response)

        elif path[0] == "share":
            self.send_file("share_preview.html", response)

        else:
            response.code = 302
            response.headers["Location"] = "/login"

    def _session(
        self, session: Session, path: list[str], response: WebResponse
    ) -> None:
        """Sends the pages the user can request while logged in

        Args:
            session (Session): The session the user is logged in as
            path (list[str]): The path the user requested
            response (WebResponse): The response to send the file to
        """

        if path[0].startswith("~"):
            # The user requested the file picker
            if path[0].lower() != f"~{session.userid}".lower():
                path[0] = f"~{session.userid}"
                response.code = 302
                response.headers["Location"] = "/" + "/".join(path)
                return

            self.send_file("file_main.html", response)
        elif path[0] == "preview":
            # The user previews a file
            self.send_file("file_preview.html", response)

        elif path[0] == "share":
            self.send_file("share_preview.html", response)

        elif path[0] == "logout":
            self._logout(session, response)

        else:
            response.code = 302
            response.headers["Location"] = f"/~{session.userid}"

    def send_file(self, name: str, response: WebResponse) -> None:
        """Sends the file to the response

        Args:
            name (str): The name of the file located in /web/
            response (WebResponse): The response to write this file to
        """

        path = os.path.join(constants.WEB, name)

        with open(path, "rb") as rf:
            response.body = rf.read()

    def _logout(self, session: Session, response: WebResponse) -> None:
        response.code = 302
        response.msg = "Logout"
        response.headers["Location"] = "/login"

        response.headers["Set-Cookie"] = (
            "session=; SameSite=Lax; HttpOnly; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
        )

        SessionStorage().remove_session(session)
