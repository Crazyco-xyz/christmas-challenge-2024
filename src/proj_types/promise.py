from ast import TypeVar
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
        self._event.wait()

        if self._data is None:
            return default

        return self._data

    def call(self, conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
        self._data = self._action(conn, cur)
        self._event.set()
