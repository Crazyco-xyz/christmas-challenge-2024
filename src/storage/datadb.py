import os
import sqlite3
import threading
from typing import Any, Type
import constants
from proj_types.promise import SQLPromise
from proj_types.singleton import singleton
from storage.files_table import FilesTable
from storage.table import Table, ShareTable
from storage.users_table import UsersTable


@singleton
class DataDB:
    TABLES: list[Type[Table]] = [
        UsersTable,
        FilesTable,
        ShareTable,
    ]

    def __init__(self, name: str = "data.db") -> None:
        self._name = name
        self._task_event = threading.Event()
        self._tasks: list[SQLPromise] = []

        threading.Thread(
            target=self._thread_main, daemon=True, name="SQLiteThread"
        ).start()

        self.add_task(SQLPromise(self._create_default_tables))

    def add_task(self, promise: SQLPromise) -> None:
        """Adds a task to the waiting task list

        Args:
            promise (SQLPromise): The task to add to the list
        """

        self._tasks.append(promise)
        self._task_event.set()

    def _thread_main(self) -> None:
        """Main method for the SQLite thread"""

        self._db = sqlite3.connect(os.path.join(constants.ROOT, self._name))
        self._cursor = self._db.cursor()

        while True:
            self._task_event.wait()

            for t in self._tasks.copy():
                t.call(self._db, self._cursor)
                self._tasks.remove(t)

            if len(self._tasks) == 0:
                self._task_event.clear()

    def _create_default_tables(
        self, conn: sqlite3.Connection, cur: sqlite3.Cursor
    ) -> None:
        """Creates all tables needed for this project"""

        # Loop through all tables
        for table_type in self.TABLES:
            table = table_type(self.add_task)

            # Create query string and execute
            query = f"CREATE TABLE IF NOT EXISTS {table.name()} ( {", ".join(table.columns())} )"

            cur.execute(query)

        # Commit all table creations
        conn.commit()

    def users(self) -> UsersTable:
        return UsersTable(self.add_task)

    def files(self) -> FilesTable:
        return FilesTable(self.add_task)

    def shares(self) -> ShareTable:
        return ShareTable(self.add_task)
