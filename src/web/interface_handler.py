import os
import constants
from web.handler import WebHandler
from web.response import WebResponse
from web.session import Session, SessionStorage
from web.socket_data import DataSender


class InterfaceHandler(WebHandler):
    def can_handle(self) -> bool:
        """
        Returns:
            bool: If the handler can handle the request
        """

        if self._request.path == None:
            return False

        # Check if the user is requesting root
        if self._request.path == "/":
            return True

        # Check if the user is requesting a page that is part of the interface
        paths = ["~", "login", "register", "preview", "share", "logout"]
        for p in paths:
            if self._request.path.startswith(f"/{p}"):
                return True

        return False

    def handle(self, response: WebResponse) -> None:
        """Handles the request

        Args:
            response (WebResponse): The response to this request
        """

        if self._request.path == None:
            return

        # Split the path into parts
        path = self._request.path.split("/")
        if len(path[0]) == 0:
            path.pop(0)

        # Tell the browser interface pages can't be cached because they are dynamic
        response.headers["Cache-Control"] = "no-store"

        # Check if the user is logged in
        if (session := self.get_session()) is None:
            self._no_session(path, response)

        else:
            self._session(session, path, response)

    def _redirect(self, location: str, response: WebResponse) -> None:
        """Redirect the user to the specified location

        Args:
            location (str): The location to redirect the user to
            response (WebResponse): The response to send the redirect to
        """

        response.code, response.msg = 302, "Temporary Redirect"
        response.headers["Location"] = location

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
            self._redirect("/login", response)

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

                self._redirect("/" + "/".join(path), response)
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
            # Redirect the user to their file picker
            self._redirect(f"/~{session.userid}", response)

    def send_file(self, name: str, response: WebResponse) -> None:
        """Sends the file to the response

        Args:
            name (str): The name of the file located in /web/
            response (WebResponse): The response to write this file to
        """

        # Get the path to the file
        path = os.path.join(constants.WEB, name)
        response.body = DataSender(path)

    def _logout(self, session: Session, response: WebResponse) -> None:
        """Logs the user out

        Args:
            session (Session): The session to log out
            response (WebResponse): The response to this request
        """

        self._redirect("/login", response)

        # Remove the session cookie
        response.headers["Set-Cookie"] = (
            "session=; SameSite=Lax; HttpOnly; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
        )

        # Remove the session from the storage
        SessionStorage().remove_session(session)
