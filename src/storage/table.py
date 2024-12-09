import abc
import sqlite3
from typing import Any, Iterable, Optional


class Table(abc.ABC):
    def __init__(self, conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
        self._conn = conn
        self._cur = cur

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
        self._cur.execute(" ".join(query), args)
        return self._cur.fetchall()

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
        self._cur.execute(" ".join(query), args)
        self._conn.commit()


class UsersTable(Table):
    def name(self) -> str:
        return "users"

    def columns(self) -> list[str]:
        return [
            "user_id TEXT PRIMARY KEY",
            "email TEXT NOT NULL UNIQUE",
            "password TEXT NOT NULL",
            "admin INTEGER",
        ]

    def exists(self, userid: str, email: str) -> bool:
        """Checks if the userid or email already exists

        Args:
            userid (str): The userid to check for
            email (str): The email to check for

        Returns:
            bool: Whether one or both already exist
        """

        return self.id_exists(userid) or self.email_exists(email)

    def email_exists(self, email: str) -> bool:
        """Checks if an email has already been taken

        Args:
            email (str): The email to test for

        Returns:
            bool: Whether the email exists
        """

        users = self.select("*", "email = ?", (email))

        return len(users) > 0

    def id_exists(self, userid: str) -> bool:
        """Checks if a UserID has already been taken

        Args:
            userid (str): The UserID to test for

        Returns:
            bool: Whether the UserID exists
        """

        users = self.select("*", "user_id = ?", (userid))

        return len(users) > 0

    def register(self, userid: str, email: str, passwd: str, admin: bool) -> bool:
        """Registers the user

        Args:
            userid (str): The name of the user
            email (str): The email of the user
            passwd (str): The hashed password of the user
            admin (bool): Whether this user is an admin

        Returns:
            bool: Whether the registration was successful
        """

        if self.exists(userid, email):
            return False

        self.insert(user_id=userid, email=email, password=passwd, admin=int(admin))
        return True

    def login(self, userid: str, passwd: str) -> bool:
        """Checks if the login credentials are correct

        Args:
            userid (str): The name of the user
            passwd (str): The hashed password of the user

        Returns:
            bool: Whether the login was successful
        """

        if not self.exists(userid, ""):
            return False

        users = self.select("*", "user_id = ? AND password = ?", (userid, passwd))

        return len(users) > 0


class FilesTable(Table):
    def name(self) -> str:
        return "files"

    def columns(self) -> list[str]:
        return [
            "file_id TEXT PRIMARY KEY",
            "user_id TEXT NOT NULL",
            "file_type INTEGER NOT NULL",
            "file_location TEXT NOT NULL",
            "file_name TEXT NOT NULL",
        ]


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
