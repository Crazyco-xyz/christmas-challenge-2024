import json
from re import L
import re
from typing import Any, Optional
from log import LOG
from storage.datadb import DataDB
from web.handler import WebHandler
from web.response import WebResponse
from web.session import SessionStorage


class APIHandler(WebHandler):
    API_PREFIX = "/a/v1/"

    def can_handle(self) -> bool:
        if self._request.path is None:
            return False

        return self._request.path.startswith(self.API_PREFIX)

    def _get_body(self) -> dict[str, Any]:
        """Tries to retrieve the body in JSON format

        Returns:
            dict[str, Any]: The retrieved body
        """

        if self._request.body is None:
            return {}

        contype = self._request.headers.get("Content-Type", "")
        if contype != "application/json":
            return {"data": (self._request.body, contype)}

        try:
            return json.loads(self._request.body)
        except json.JSONDecodeError:
            LOG.debug("Could not decode JSON %s", self._request.body)
            return {}

    def handle(self, response: WebResponse) -> None:
        if self._request.path is None:
            return

        # Load path and json body
        path = self._request.path[len(self.API_PREFIX) :].split("/")
        body: dict[str, Any] = self._get_body()

        if path[0] == "register":
            self._register(body, response)
        elif path[0] == "login":
            self._login(body, response)

    def _check_email(self, email: str) -> bool:
        """Checks the provided Email address

        Args:
            email (str): The Email address to check

        Returns:
            bool: Whether this address is valid
        """

        return re.search(r"^\S+@\S+\.\S+$", email) is not None

    def _response_invalid_data(self, response: WebResponse, message: str) -> None:
        """Modifies the response for invalid data

        Args:
            response (WebResponse): The response to modify
            message (str): The message to show to the user
        """

        response.code = 400
        response.msg = "Invalid Data"
        response.json_body({"message": message})

    def _register(self, body: dict[str, Any], response: WebResponse) -> None:
        """Registers the user with the provided data

        Args:
            body (dict[str, Any]): The body containing user data
            response (WebResponse): The response to this request
        """

        userdb = DataDB().users()

        # Read user data
        userid = body.get("userid", None)
        email = body.get("email", None)
        password = body.get("passwd", None)

        # Check user data
        if userid is None or len(userid) < 3:
            self._response_invalid_data(
                response, "The User ID has to be at least 3 characters long!"
            )
            return

        if userdb.id_exists(userid):
            self._response_invalid_data(response, "This User ID is already taken!")
            return

        if email is None or not self._check_email(email):
            self._response_invalid_data(response, "Invalid Email address!")
            return

        if userdb.email_exists(email):
            self._response_invalid_data(
                response, "This Email address is already taken!"
            )
            return

        if password is None:
            self._response_invalid_data(response, "Failed to transmit password!")
            return

        # Register user using data
        userdb.register(userid, email, password, False)

    def _login(self, body: dict[str, Any], response: WebResponse) -> None:
        """Logs the user in using the provided user data

        Args:
            body (dict[str, Any]): The body containing user data
            response (WebResponse): The response to this request
        """

        # Read user data
        userid = body.get("userid", None)
        password = body.get("passwd", None)

        # Check user data
        if userid is None:
            self._response_invalid_data(response, "Please provide a User ID!")
            return

        if password is None:
            self._response_invalid_data(response, "Failed to transmit password!")
            return

        # Try to log in
        session = SessionStorage().create_session(self._request.ip, userid, password)

        if session is None:
            self._response_invalid_data(
                response, "Could not login with these credentials!"
            )
            return

        # Set the session cookie
        response.headers["Set-Cookie"] = (
            f"session={session.session_id}; SameSite=Lax; HttpOnly"
        )
