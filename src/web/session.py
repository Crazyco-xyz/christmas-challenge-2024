import hashlib
import time
from typing import Optional
from proj_types.singleton import singleton


@singleton
class SessionStorage:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self, ip: str, name: str, passwd: str) -> "Optional[Session]":
        """Creates a session for the user and stores it

        Args:
            ip (str): The IP of the request
            name (str): The name/userid to login with
            passwd (str): The hashed password

        Returns:
            Session: The session created for this IP
        """

        from storage.datadb import DataDB

        # Check if user/passwd combo is correct
        if not DataDB().users().login(name, passwd):
            return None

        # Create session for user
        session = Session(ip, name)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, ip: str, sessid: str) -> "Optional[Session]":
        """Gets the session for an IP

        Args:
            ip (str): The IP of the request
            sessid (str): The session ID stored in the session cookie

        Returns:
            Optional[Session]: The session or None is the session is not valid
        """

        # Check if we know this session id
        if sessid not in self._sessions:
            return None

        # Check if the IP is what we expect for this session
        session = self._sessions[sessid]
        if session.ip != ip:
            return None

        # Check if the session expired
        if session.expired:
            del self._sessions[sessid]
            return None

        return session

    def remove_session(self, session: "Session") -> None:
        """Removes a session from the storage

        Args:
            session (Session): The session to remove
        """

        del self._sessions[session.session_id]


class Session:
    def __init__(self, ip: str, userid: str, expires_after: int = 172800) -> None:
        self._ip: str = ip
        self._userid: str = userid
        t = time.time()
        self._session: str = self._make_session_id(t)
        self._expires: float = t + expires_after

    def _make_session_id(self, t: float) -> str:
        """Creates a session ID using the userid, ip and time

        Args:
            t (float): The current time

        Returns:
            str: The created session ID
        """

        hash_in = f"{self._userid}{self._ip}{time.time()}"
        return hashlib.sha256(hash_in.encode()).hexdigest()

    @property
    def ip(self) -> str:
        """
        Returns:
            str: The IP from which the device logged in
        """

        return self._ip

    @property
    def userid(self) -> str:
        """
        Returns:
            str: The username who this session belongs to
        """

        return self._userid

    @property
    def session_id(self) -> str:
        """
        Returns:
            str: The ID given to this session
        """

        return self._session

    @property
    def expired(self) -> bool:
        """
        Returns:
            bool: Whether the session is expired
        """

        return time.time() > self._expires
