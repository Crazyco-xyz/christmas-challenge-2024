import os
import sqlite3
from typing import Type
import constants
from proj_types.singleton import singleton
from storage.table import Table, UsersTable, FilesTable, ShareTable


@singleton
class DataDB:
    TABLES: list[Type[Table]] = [
        UsersTable,
        FilesTable,
        ShareTable,
    ]

    def __init__(self, name: str = "data.db") -> None:
        self._db = sqlite3.connect(os.path.join(constants.ROOT, name))
        self._cursor = self._db.cursor()

        self._create_default_tables()

    def _create_default_tables(self) -> None:
        """Creates all tables needed for this project"""

        # Loop through all tables
        for table_type in self.TABLES:
            table = table_type(self._db, self._cursor)

            # Create query string and execute
            query = f"CREATE TABLE IF NOT EXISTS {table.name()} ( {", ".join(table.columns())} )"

            self._cursor.execute(query)

        # Commit all table creations
        self._db.commit()

    def users(self) -> UsersTable:
        return UsersTable(self._db, self._cursor)

    def files(self) -> FilesTable:
        return FilesTable(self._db, self._cursor)

    def shares(self) -> ShareTable:
        return ShareTable(self._db, self._cursor)
