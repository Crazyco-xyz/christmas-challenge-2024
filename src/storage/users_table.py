from storage.table import Table


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

        users = self.select("*", "email = ?", (email,))

        return len(users) > 0

    def id_exists(self, userid: str) -> bool:
        """Checks if a UserID has already been taken

        Args:
            userid (str): The UserID to test for

        Returns:
            bool: Whether the UserID exists
        """

        users = self.select("*", "user_id = ?", (userid,))

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
