import abc
import sqlite3
from typing import Any, Callable, Optional

from proj_types.promise import SQLPromise


class Table(abc.ABC):
    def __init__(self, task_callback: Callable[[SQLPromise], None]) -> None:
        self._task_callback = task_callback

    @abc.abstractmethod
    def name(self) -> str:
        """
        Returns:
            str: The name of the table used in SQL
        """

        pass

    @abc.abstractmethod
    def columns(self) -> list[str]:
        """
        Returns:
            list[str]: The column definitions used for creating the table
        """

        pass

    def execute_fetch(self, query: str, args=()) -> Callable[[list[str]], list[str]]:
        def _execute(_: sqlite3.Connection, cur: sqlite3.Cursor) -> list[str]:
            cur.execute(query, args)
            return cur.fetchall()

        promise = SQLPromise(_execute)
        self._task_callback(promise)
        return promise.wait

    def execute_commit(self, query: str, args=()) -> Callable[[None], None]:
        def _execute(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
            cur.execute(query, args)
            conn.commit()

        promise = SQLPromise(_execute)
        self._task_callback(promise)
        return promise.wait

    def select(self, columns: str, where: Optional[str], args=()) -> list[Any]:
        """Simplifies a SELECT request

        Args:
            columns (str): The columns to select (like *)
            where (Optional[str]): The WHERE part of the SQL query
            args (tuple, optional): The arguments to insert into the query. Defaults to ().

        Returns:
            list[Any]: All selected items
        """

        # Prepare query
        query = ["SELECT", columns, "FROM", self.name()]

        # Append WHERE part if exists
        if where is not None:
            query.append("WHERE")
            query.append(where)

        # Execute query and fetch results
        return self.execute_fetch(" ".join(query), args)([])

    def insert(self, **items: Any) -> None:
        """Simplifies an INSERT INTO this table

        Args:
            **items (dict[str, Any]): The items to insert"""

        # Prepare the query and arguments
        query = ["INSERT INTO", self.name(), "("]
        args = [v for _, v in items.items()]

        # Insert names of values to insert
        query.append(", ".join([k for k, _ in items.items()]))

        query.append(") VALUES (")

        # Insert `?` characters for arguments to be inserted
        query.append(", ".join(["?" for _ in range(len(items))]))

        query.append(")")

        # Execute the query
        self.execute_commit(" ".join(query), args)(None)

    def update(self, set: str, where: Optional[str], args=()) -> None:
        """Updates a row in the table

        Args:
            set (str): The SET part of the query
            where (Optional[str]): The WHERE part of the query
            args (tuple, optional): Arguments. Defaults to ().
        """

        query = ["UPDATE", self.name(), "SET", set]

        if where:
            query.append("WHERE")
            query.append(where)

        self.execute_commit(" ".join(query), args)(None)

    def delete(self, where: str, args=()) -> None:
        """Deletes a row from the table

        Args:
            where (str): The WHERE part of the query
            args (tuple, optional): Arguments. Defaults to ().
        """

        query = ["DELETE FROM", self.name(), "WHERE", where]

        self.execute_commit(" ".join(query), args)(None)


class ShareTable(Table):
    def name(self) -> str:
        return "share"

    def columns(self) -> list[str]:
        return [
            "share_id TEXT PRIMARY KEY",
            "creator_id TEXT NOT NULL",
            "receiver_id TEXT",
            "password TEXT",
            "expiration REAL NOT NULL",
        ]
