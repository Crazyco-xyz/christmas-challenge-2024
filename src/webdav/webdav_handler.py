import base64
import hashlib
import mimetypes
import os
from typing import Optional

import constants
from log import LOG
from proj_types.proto_error import ProtocolError
from proj_types.webmethod import WebMethod
from storage.datadb import DataDB
from web.handler import WebHandler
from web.response import WebResponse
from web.session import Session, SessionStorage
from web.socket_data import DataReceiver, DataSender
from webdav.properties import DavProp, DavProperties
from proj_types.xml import XmlFragment, XmlReader, XmlString

type FileDict = dict[str, str | FileDict]


class WebDavHandler(WebHandler):
    def can_handle(self) -> bool:
        if self._request.method is None:
            return False

        if self._request.method in [
            WebMethod.PROPFIND,
            WebMethod.MKCOL,
            WebMethod.DELETE,
            WebMethod.PUT,
            WebMethod.COPY,
            WebMethod.PROPPATCH,
            WebMethod.MOVE,
            WebMethod._LOCK,
            WebMethod._UNLOCK,
        ]:
            return True

        if (
            self._request.method == WebMethod.GET
            and len(self._request.headers.get("Authorization", "")) > 0
        ):
            return True

        return False

    def _request_auth(self, response: WebResponse) -> None:
        """Sends a response requesting authentication

        Args:
            response (WebResponse): The response to send to
        """

        response.code, response.msg = 401, "Authenticate"
        response.headers["WWW-Authenticate"] = (
            f'Basic realm="{constants.DAV_REALM}", charset="UTF-8"'
        )

    def _login(self, response: WebResponse) -> Optional[Session]:
        """Tries to login the request using the credentials provided

        Args:
            response (WebResponse): The response to send errors to

        Returns:
            Optional[Session]: The session or None if no login occurred
        """

        # Get the Authorization HTTP header
        authorization = self._request.headers.get("Authorization", "")
        if not authorization.startswith("Basic "):
            self._request_auth(response)
            return

        # Decode the credential part of the header
        creds = base64.standard_b64decode(authorization[6:]).decode()

        # Checks if there is a password
        if ":" not in creds:
            self._request_auth(response)

        # Splits the credentials into userid and password
        userid, passwd = creds.split(":", 1)

        # Tries to login user
        sess = SessionStorage().create_session(
            self._request.ip, userid, hashlib.sha512(passwd.encode()).hexdigest()
        )

        # Request authentication again if user could not be logged in
        if sess is None:
            self._request_auth(response)
            return

        return sess

    def _read_body(self, response: WebResponse) -> Optional[XmlFragment]:
        """Reads the XML body of the request

        Args:
            response (WebResponse): The response to send errors to

        Returns:
            Optional[XmlFragment]: The XML data or None if none encountered
        """

        # Check if we have a body
        if self._request.body is None:
            return None

        # Check if the body is application/xml or text/xml
        content_type = self._request.headers.get("Content-Type", "").split(";", 1)[0]
        if not content_type.endswith("/xml"):

            # If we are getting a PUT request different bodies are ok
            if self._request.method == WebMethod.PUT:
                return None

            # Tell the client we dont understand the body
            response.code, response.msg = 415, "Unsupported Body"
            return

        # Check if the data is too large to receive instantly
        if isinstance(self._request.body, DataReceiver):
            return None

        elif isinstance(self._request.body, bytes):
            body = self._request.body

        else:
            body = bytes(self._request.body)

        # Read the body as XML
        reader = XmlReader(body.decode())
        return reader.read(None)

    def handle(self, response: WebResponse) -> None:
        """Handles the request

        Args:
            response (WebResponse): The response to this request
        """

        # Read body
        if (xml := self._read_body(response)) is None:
            xml = XmlFragment("empty", None)

        # Read credentials
        if (session := self._login(response)) is None:
            return

        # Split the path into a list
        path: list[str] = []
        if self._request.path is not None and self._request.path != "/":
            path = self._request.path.strip("/").split("/")

        # Execute the request
        try:
            match self._request.method:
                case WebMethod.PROPFIND:
                    self._propfind(path, xml, session, response)
                case WebMethod.MKCOL:
                    self._mkcol(path, session, response)
                case WebMethod.DELETE:
                    self._delete(path, session, response)
                case WebMethod.PUT:
                    self._put(path, self._request.body or b"", session, response)
                case WebMethod.COPY:
                    self._copy(path, session, response)
                case WebMethod.PROPPATCH:
                    self._proppatch(path, session, xml, response)
                case WebMethod.MOVE:
                    self._move(path, session, response)
                case WebMethod.GET:
                    self._get(path, session, response)

                case _:
                    self._method_not_supported(response)

        except ProtocolError as e:
            LOG.warning("Protocol error: %s", e.desc)
            response.code, response.msg = 400, "Protocol Error"
            return

    def _method_not_supported(self, response: WebResponse) -> None:
        """Sends a response that the method is not supported

        Args:
            response (WebResponse): The response to send to
        """

        response.code, response.msg = 405, "Method Not Allowed"

        response.headers["Allow"] = ", ".join(
            [
                e.value
                for n, e in WebMethod._member_map_.items()
                if not n.startswith("_")
            ]
        )
        response.headers["DAV"] = "1, 2"

    def _check_not_root(self, path: list[str], response: WebResponse) -> bool:
        """Checks if the user tries to access the root directory and sends an error if so

        Args:
            path (list[str]): The path to check
            response (WebResponse): The response to send the error to

        Returns:
            bool: Whether the user tries to access the root directory or not
        """

        if len(path) != 0:
            return False

        response.code, response.msg = 403, "Forbidden"
        return True

    def _folder_by_path(
        self, session: Session, path: list[str], response: WebResponse
    ) -> Optional[tuple[str, dict[str, str | dict]]]:
        """Gets a folder and ID from the path sent by the client

        Args:
            session (Session): The session of the user
            path (list[str]): The path to search for
            response (WebResponse): The response to send errors to

        Returns:
            Optional[tuple[str, dict[str, str | dict]]]: The id and current dir, if it was found. None otherwise
        """

        file_db = DataDB().files()
        root = file_db.list_all(session)
        file_id = ""

        # Check if we are in the root directory
        if len(path) == 0:
            return (file_id, root)

        # Go through every path segment
        for p in path:

            # Go through every element inside current directory
            for eid, element in root.items():

                # Check if we found the directory referred to by p
                if isinstance(element, dict) and element.get("_name", None) == p:
                    file_id = eid
                    root = element
                    break
            else:

                # We did not find any matching path segment, send error
                response.code, response.msg = 404, "Not Found"
                return None

        return file_id, root

    def _search_file(
        self, dir: FileDict, file_name: str, response: WebResponse
    ) -> Optional[tuple[bool, str]]:
        """Searches for a file or folder inside the directory

        Args:
            dir (FileDict): The directory to search in
            file_name (str): The name of the file to search for
            response (WebResponse): The response to send errors to

        Returns:
            Optional[tuple[bool, str]]: A tuple of (is_file, file_id) or None if no file is found
        """

        for file_id, el in dir.items():
            if isinstance(el, dict) and el.get("_name") == file_name:

                # Found a folder with this name
                return False, file_id
            elif el == file_name:

                # Found a file with this name
                return True, file_id

        # No file found
        response.code, response.msg = 404, "Not found"
        return None

    def _get_depth(self) -> int:
        """Gets the value of the depth header

        Returns:
            int: The depth of the header or -1
        """

        match self._request.headers.get("Depth", ""):
            case "0":
                return 0
            case "1":
                return 1
            case _:
                return -1

    def _propfind_props(self, xml: XmlFragment) -> list[DavProp]:
        """Lists the properties requested by the client

        Args:
            xml (XmlFragment): The XML data containing the requested properties

        Returns:
            list[DavProp]: The requested properties
        """

        # Check if we have a PROPFIND XML body
        has_data = xml.name == "propfind"

        if not has_data:
            return DavProperties.allprop()

        # List all properties requested by the client
        properties = []

        if xml.children[0].name == "prop":
            xml = xml.children[0]

        for c in xml.children:
            if c.name == "allprop":
                properties.extend(DavProperties.allprop())
            else:
                p = DavProperties.get_prop(c.name)
                if p is not None:
                    properties.append(p)

        return properties

    def _propfind(
        self, path: list[str], xml: XmlFragment, session: Session, response: WebResponse
    ) -> None:
        """Executes a PROPFIND request on path

        Args:
            path (list[str]): The path to execute the request on
            xml (XmlFragment): The XML body
            session (Session): The user's session
            response (WebResponse): The response to this request

        Raises:
            ProtocolError: For inconsistencies with the protocol
        """

        # Check if the user tries to access root
        if len(path) == 0:

            # Get the directory listing
            if (current_dir := self._folder_by_path(session, path, response)) is None:
                return

            is_file, file_id = False, None
            dir_list = current_dir[1]
        else:

            # Get the directory listing of the parent dir
            dir_part = path[:-1]
            file_name = path[-1]

            # Get the directory listing
            if (
                current_dir := self._folder_by_path(session, dir_part, response)
            ) is None:
                return

            # Search the parent directory for the file/folder requested
            if (
                target := self._search_file(current_dir[1], file_name, response)
            ) is None:
                return

            is_file, file_id = target
            dir_list = current_dir[1][file_id] if not is_file else current_dir[1]

            if not isinstance(dir_list, dict):
                dir_list = current_dir[1]

        # Get the properties requested by the client
        properties = self._propfind_props(xml)

        # Create the multistatus response fragment
        xml_resp = XmlFragment("multistatus", "D")
        xml_resp.properties["xmlns:D"] = "DAV:"

        # PROPFIND the current directory/file to the depth of `depth`
        if is_file:
            self._propfind_file(
                path[:-1],
                file_id or "",
                path[-1],
                properties,
                xml_resp,
            )
        else:
            self._propfind_dir(
                file_id,
                dir_list,
                path,
                properties,
                xml_resp,
                self._get_depth(),
            )

        # Send the multistatus response
        response.code, response.msg = 207, "Multi-Status"
        response.body = XmlFragment.stringify(xml_resp).encode()
        response.headers["Content-Type"] = "application/xml"

    def _list_properies(
        self, file_id: Optional[str], properties: list[DavProp]
    ) -> XmlFragment:
        """Lists all requested properties of a file/folder

        Args:
            file_id (str): The file/folder to list properties on or None for root
            properties (list[DavProp]): The properties requested by the client

        Returns:
            XmlFragment: The fragment containing all properties
        """

        # Get all properties
        children = []
        for p in properties:
            if p.possible_for(file_id):
                if file_id:
                    c = p.get_property(file_id)
                else:
                    c = p.root_property()
                children.append(c)

        # Make propstat fragment
        propstat = XmlFragment("propstat", "D")
        propstat.children.append(XmlFragment("prop", "D", children))
        propstat.children.append(
            XmlFragment("status", "D", [XmlString("HTTP/1.1 200 OK")])
        )

        return propstat

    def _propfind_file(
        self,
        current_path: list[str],
        file_id: str,
        file_name: str,
        properties: list[DavProp],
        xml_resp: XmlFragment,
    ) -> None:
        """Executes a PROPFIND request on a file

        Args:
            current_path (list[str]): The current path
            file_id (str): The ID of the file
            file_name (str): The name of the file
            properties (list[DavProp]): The properties requested by the client
            xml_resp (XmlFragment): The XML response to write to
        """

        # Create the href string
        href = f"/{ '/'.join(current_path) }{ '/' if current_path else '' }{ file_name}"
        href = href.replace(" ", "%20")

        # Create the response fragment
        file_resp = XmlFragment(
            "response",
            "D",
            [
                XmlFragment("href", "D", [XmlString(href)]),
                self._list_properies(file_id, properties),
            ],
        )

        # Append the response fragment to the multistatus response
        xml_resp.children.append(file_resp)

    def _propfind_dir(
        self,
        current_id: Optional[str],
        dir: FileDict,
        current_path: list[str],
        properties: list[DavProp],
        xml_resp: XmlFragment,
        depth: int,
    ) -> None:
        """Executes a PROPFIND request on a directory

        Args:
            current_id (Optional[str]): The ID of the directory
            dir (FileDict): The contents of the directory
            current_path (list[str]): The current path
            properties (list[DavProp]): The properties requested by the client
            xml_resp (XmlFragment): The XML response to write to
            depth (int): The depth to search to
        """

        # List properties for parent directory
        href = f"/{"/".join(current_path)}".replace(" ", "%20")

        dir_resp = XmlFragment(
            "response",
            "D",
            [
                XmlFragment("href", "D", [XmlString(href)]),
                self._list_properies(current_id, properties),
            ],
        )
        xml_resp.children.append(dir_resp)

        # Check if we have reached max depth
        if depth == 0:
            return

        # Go through contents of dir
        for file_id, el in dir.items():
            if file_id == "_name":
                continue

            # Check if we encountered a dir
            if isinstance(el, dict):
                # PROPFIND the directory
                self._propfind_dir(
                    file_id,
                    el,
                    [*current_path, str(el.get("_name", ""))],
                    properties,
                    xml_resp,
                    depth - 1,
                )
                continue

            # List properties of the file
            self._propfind_file(current_path, file_id, el, properties, xml_resp)

    def _mkcol(self, path: list[str], session: Session, response: WebResponse) -> None:
        """Creates a folder at path

        Args:
            path (list[str]): The path of the collection to create
            session (Session): The session of the user
            response (WebResponse): The response to this request
        """

        # Check if the user tries to create root
        if self._check_not_root(path, response):
            return

        # Split path into known and new part
        known_path = path[:-1]
        new_dir = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, known_path, response)) is None:
            return

        # Create the collection
        DataDB().files().make_folder(session, current_dir[0], new_dir)

        response.code, response.msg = 201, "Created"

    def _delete(self, path: list[str], session: Session, response: WebResponse) -> None:
        """Deletes a file or folder

        Args:
            path (list[str]): The path to delete
            session (Session): The session of the user
            response (WebResponse): The response to this request
        """

        # Check if the user tries to delete root
        if self._check_not_root(path, response):
            return

        # Split the path into known and file/folder part
        known_part = path[:-1]
        file_name = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, known_part, response)) is None:
            return

        # Check the current folder for the file/folder to delete
        if (search := self._search_file(current_dir[1], file_name, response)) is None:
            return
        _, delete_id = search

        file_db = DataDB().files()

        # Check if the user has access to the file/folder
        if not file_db.can_download(session, delete_id):
            response.code, response.msg = 403, "Forbidden"
            return

        # Delete the file/folder
        file_db.delete_file(delete_id)

        response.code, response.msg = 204, "No Content"

    def _put(
        self,
        path: list[str],
        body: bytes | DataReceiver,
        session: Session,
        response: WebResponse,
    ) -> None:
        """Uploads a new file to the server or replaces an existing file

        Args:
            path (list[str]): The path to write the file to
            body (bytes | DataReceiver): The file to write
            session (Session): The session of the user
            response (WebResponse): The response to this request
        """

        # Check if the user tries to put root
        if self._check_not_root(path, response):
            return

        # Split the path into folder and file
        known_path = path[:-1]
        file_name = path[-1]

        # Get the current folder
        if (current_dir := self._folder_by_path(session, known_path, response)) is None:
            return

        # Check if we already have the file
        for test_id, name in current_dir[1].items():
            if name == file_name:
                file_id = test_id
                break
        else:
            # Otherwise create the file
            file_id = DataDB().files().make_file(session, current_dir[0], file_name)

        # Write the contents to the file
        with open(os.path.join(constants.FILES, file_id), "wb") as rf:
            if isinstance(body, DataReceiver):
                body.receive_into(rf)
            else:
                rf.write(body)

        response.code, response.msg = 201, "Created"

    def _copy_file(
        self, session: Session, source_id: str, target_dir: str, target_name: str
    ) -> None:
        """Copies one file to a new location with a new name

        Args:
            session (Session): The session to copy files in
            source_id (str): The ID of the source file
            target_dir (str): The ID of the target dir
            target_name (str): The name of the target
        """

        # Create the new file
        target_id = DataDB().files().make_file(session, target_dir[0], target_name)

        # Copy the contents of the file
        self._copy_file_contents(source_id, target_id)

    def _copy_file_contents(self, source_id: str, target_id: str) -> None:
        """Copies the file contents of a file to another

        Args:
            source_id (str): The file to copy from
            target_id (str): The file to copy to
        """

        # Open source file
        with open(os.path.join(constants.FILES, source_id), "rb") as source:

            # Open target file
            with open(os.path.join(constants.FILES, target_id), "wb") as target:

                # Copy the contents
                while len(data := source.read(constants.BUFFERED_CHUNK_SIZE)) == 0:
                    target.write(data)

    def _copy_dir(
        self, session: Session, source_id: str, target_id: str, target_name: str
    ) -> None:
        """Copies a directory to a new location with a new name

        Args:
            session (Session): The session of the user
            source_id (str): The ID of the source directory
            target_id (str): The ID of the target directory's parent
            target_name (str): The name of the new directory
        """

        file_db = DataDB().files()

        # Create new and get listing of old directory
        source_dir = file_db.list_all(session, source_id)
        target_dir = file_db.make_folder(session, target_id, target_name)

        # Go through all files and directories in the source directory
        for file_id, el in source_dir.items():
            if isinstance(el, dict):
                # If the element is a directory, copy it whole
                self._copy_dir(session, file_id, target_dir, str(el.get("_name", "")))

            else:
                # If the element is a file, copy it
                self._copy_file(session, file_id, target_dir, el)

    def _copy(self, path: list[str], session: Session, response: WebResponse) -> None:
        """Copies a file or folder to a new destination

        Args:
            path (list[str]): The path of the file or folder to copy
            session (Session): The session of the user
            response (WebResponse): The response to this request
        """

        # Check if the user tries to copy root
        if self._check_not_root(path, response):
            return

        # Split the path into known and file/folder part
        known_part = path[:-1]
        file_name = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, known_part, response)) is None:
            return

        # Check the current folder for the file/folder to copy
        if (search := self._search_file(current_dir[1], file_name, response)) is None:
            return
        is_file, file_id = search

        # Get the destination
        target = self._request.headers["Destination"].strip("/").split("/")
        localip = self._request.headers.get("Host", "")

        # Strip the domain off the destination
        if "" in target:
            while target[0] != localip:
                target.pop(0)
            target.pop(0)

        # Split the destination into known and new part
        known_target = target[:-1]
        target_name = target[-1]

        # Get the target directory
        if (
            target_dir := self._folder_by_path(session, known_target, response)
        ) is None:
            return

        if is_file:
            # If the user wants to copy one file, just copy it
            self._copy_file(session, file_id, target_dir[0], target_name)

        else:
            # Otherwise copy the whole directory
            self._copy_dir(session, file_id, target_dir[0], target_name)

    def _proppatch(
        self, path: list[str], session: Session, xml: XmlFragment, response: WebResponse
    ) -> None:
        """Modifies a property of a file

        Args:
            path (list[str]): The path of the file
            session (Session): The session of the user
            xml (XmlFragment): The XML containing all properties to set
            response (WebResponse): The response to this request

        Raises:
            ProtocolError: _description_
        """

        # Check if the body matches the method
        if xml.name != "propertyupdate":
            raise ProtocolError("propertyupdate XML expected for PROPPATCH")

        # Check if the user tries to patch root
        if self._check_not_root(path, response):
            return

        # Split the path into known and file part
        dir_part = path[:-1]
        file_part = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, dir_part, response)) is None:
            return

        # Check the current folder for the file to change properties of
        if (search := self._search_file(current_dir[1], file_part, response)) is None:
            return
        _, file_id = search

        # Get the part of the XML which contains the properties
        set_xml = xml.children[0]
        prop_xml = set_xml.children[0]

        # Go through all properties
        for c in prop_xml.children:

            prop = DavProperties.get_prop(c.name)
            if prop is not None and len(c.children) > 0:

                # Check if the target supports this property
                if prop.possible_for(file_id):

                    # Set the property to the new value
                    prop.set_property(file_id, c.children[0])

    def _move(self, path: list[str], session: Session, response: WebResponse) -> None:
        """Moves a file or folder into a new directory with a new name

        Args:
            path (list[str]): The path of the file or folder to move
            session (Session): The session of the user
            response (WebResponse): The response to this request
        """

        # Check if the user tries to move root
        if self._check_not_root(path, response):
            return

        # Split the path into known and file part
        known_part = path[:-1]
        file_name = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, known_part, response)) is None:
            return

        # Check the current folder for the file to move
        if (search := self._search_file(current_dir[1], file_name, response)) is None:
            return
        _, file_id = search

        # Get the destination
        target = self._request.headers["Destination"].strip("/").split("/")
        localip = self._request.headers.get("Host", "")

        # Strip the domain off the destination
        if "" in target:
            while target[0] != localip:
                target.pop(0)
            target.pop(0)

        # Split the destination into known and new part
        known_target = target[:-1]
        target_name = target[-1]

        # Get the target directory
        if (
            target_dir := self._folder_by_path(session, known_target, response)
        ) is None:
            return

        # Move the file
        file_db = DataDB().files()
        file_db.move(file_id, target_dir[0])
        file_db.rename(file_id, target_name)

    def _get(self, path: list[str], session: Session, response: WebResponse) -> None:
        """Downloads the content of a file

        Args:
            path (list[str]): The path to the file to download
            session (Session): The session of the user
            response (WebResponse): The response to send the file to

        Raises:
            ProtocolError: When trying to download folders
        """

        # Check if the user tries to download root
        if self._check_not_root(path, response):
            return

        # Split the path into known and file part
        known_part = path[:-1]
        file_name = path[-1]

        # Get the current directory
        if (current_dir := self._folder_by_path(session, known_part, response)) is None:
            return

        # Check the current folder for the file to download
        if (search := self._search_file(current_dir[1], file_name, response)) is None:
            return
        is_file, file_id = search

        # Check if the file is a folder
        if not is_file:
            raise ProtocolError("Downloading of folders is not supported")

        # Get the file name
        file_name = DataDB().files().get_name(file_id)

        # Modify the response to download the file
        response.headers["Content-Type"] = (
            mimetypes.guess_type(file_name)[0] or constants.MIME_FALLBACK
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{file_name}"'

        response.body = DataSender(os.path.join(constants.FILES, file_id))
