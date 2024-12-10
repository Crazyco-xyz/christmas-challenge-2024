import json
import mimetypes
import os
import re
from typing import Any, Optional

import constants
from log import LOG
from storage.datadb import DataDB
from web.handler import WebHandler
from web.response import WebResponse
from web.session import Session, SessionStorage


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

        elif path[0] == "upload":
            self._upload(path, self._request.body or b"", response)

        elif path[0] == "rename":
            self._rename(body, response)

        elif path[0] == "move":
            self._move(body, response)

        elif path[0] == "delete":
            self._delete(body, response)

        elif DataDB().files().check_file_id(path[0]):
            # User requests contents of a file
            self._download(path, response)

    def _check_email(self, email: str) -> bool:
        """Checks the provided Email address

        Args:
            email (str): The Email address to check

        Returns:
            bool: Whether this address is valid
        """

        return re.search(r"^\S+@\S+\.\S+$", email) is not None

    def _check_login(self, response: WebResponse) -> Optional[Session]:
        session = self.get_session()
        if session is None:
            self._response_invalid_data(response, "You need to login.")
            return None

        return session

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
            f"session={session.session_id}; SameSite=Lax; HttpOnly; Path=/"
        )

    def _upload(self, path: list[str], body: bytes, response: WebResponse) -> None:
        """Performs a file upload

        Args:
            path (list[str]): The path the user requested
            body (bytes): The raw file (body) in bytes
            response (WebResponse): The response to this request
        """

        # Check if the user is logged in
        if not (session := self._check_login(response)):
            return

        if len(path) == 2:
            # We do not have a parent dir
            parent_dir: str = ""
            file_name: str = path[1]
        elif len(path) > 2:
            # We have a parent dir
            parent_dir: str = path[1]
            file_name: str = path[2]
        else:
            # We do not even have a file
            self._response_invalid_data(response, "Invalid Data.")
            return

        # Enter file into database
        file_id = DataDB().files().make_file(session, parent_dir, file_name)

        # Write file to disk
        with open(os.path.join(constants.FILES, file_id), "wb") as file:
            file.write(body)

        # Respond with the file_id for JS
        response.json_body({"file_id": file_id})

    def _download(self, path: list[str], response: WebResponse) -> None:
        """Performs a file download

        Args:
            path (list[str]): The path containing the file the user wants
            response (WebResponse): The response to download with
        """

        # Check if the user is logged in
        if not (session := self._check_login(response)):
            return

        # Check if user has permissions to download file
        file_db = DataDB().files()
        file_id = path[0]
        if not file_db.can_download(session, file_id):
            self._response_invalid_data(response, "You cannot download this file!")
            return

        if file_db.check_folder_id(file_id):
            self._response_invalid_data(response, "You cannot download a folder!")
            return

        # Download file
        with open(os.path.join(constants.FILES, file_id), "rb") as rf:
            response.body = rf.read()

        # Guess MIME type for browser (defaults to `application/octet-stream`)
        response.headers["Content-Type"] = (
            mimetypes.guess_type(file_db.get_name(file_id))[0]
            or "application/octet-stream"
        )

    def _rename(self, body: dict[str, Any], response: WebResponse) -> None:
        """Renames a file selected in the body to a new name

        Args:
            body (dict[str, Any]): The data for renaming
            response (WebResponse): The response to this request
        """

        # Check if the user is logged in
        if not (session := self._check_login(response)):
            return

        file_db = DataDB().files()

        file_id = body.get("file_id", None)
        new_name = body.get("new_name", None)

        # Check if the file exists
        if file_id is None or not file_db.check_file_id(file_id):
            self._response_invalid_data(response, "File does not exist.")
            return

        # Check if the user has access to the file
        if not file_db.can_download(session, file_id):
            self._response_invalid_data(response, "You can't do that!")
            return

        # Check if the new name is valid
        if new_name is None or len(new_name) == 0:
            self._response_invalid_data(response, "No new name specified!")
            return

        file_db.rename(file_id, new_name)

    def _move(self, body: dict[str, Any], response: WebResponse) -> None:
        """Moves a file into a new folder

        Args:
            body (dict[str, Any]): The file and folder data
            response (WebResponse): The response to this request
        """

        # Check if the user is logged in
        if not (session := self._check_login(response)):
            return

        file_db = DataDB().files()

        file_id = body.get("file_id", None)
        new_path = body.get("folder_id", None)

        # Check if file exists
        if file_id is None or not file_db.check_file_id(file_id):
            self._response_invalid_data(response, "File does not exist.")
            return

        # Check if user has access to file
        if not file_db.can_download(session, file_id):
            self._response_invalid_data(response, "You can't do that!")

        # Check if folder exists
        if new_path is None or not (
            file_db.check_folder_id(new_path) or len(new_path) == 0
        ):
            self._response_invalid_data(response, "The target path does not exist.")
            return

        # Move the file
        file_db.move(file_id, new_path)

    def _delete(self, body: dict[str, Any], response: WebResponse) -> None:
        """Deletes a file

        Args:
            body (dict[str, Any]): The data of the file
            response (WebResponse): The response to this request
        """

        # Check if the user is logged in
        if not (session := self._check_login(response)):
            return

        file_db = DataDB().files()
        file_id = body.get("file_id", None)

        if file_id is None or not file_db.check_file_id(file_id):
            self._response_invalid_data(response, "File does not exist.")
            return

        if not file_db.can_download(session, file_id):
            self._response_invalid_data(response, "You can't do that!")

        file_db.delete_file(file_id)
        os.remove(os.path.join(constants.FILES, file_id))
