import sqlite3
import threading
from typing import Callable, Optional


class SQLPromise[_T]:
    def __init__(
        self, action: Callable[[sqlite3.Connection, sqlite3.Cursor], _T]
    ) -> None:
        self._event = threading.Event()
        self._action = action
        self._data: Optional[_T] = None

    def wait(self, default: _T) -> _T:
        """Wait for the promise to be resolved and return the result

        Args:
            default (_T): The default value to return if the promise is not resolved

        Returns:
            _T: The result of the promise
        """

        self._event.wait()

        if self._data is None:
            return default

        return self._data

    def call(self, conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
        """Call the action and notify waiting threads

        Args:
            conn (sqlite3.Connection): The connection to the database
            cur (sqlite3.Cursor): The cursor of database
        """

        self._data = self._action(conn, cur)
        self._event.set()
