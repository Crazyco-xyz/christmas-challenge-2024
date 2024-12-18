from typing import Optional
from uuid import uuid4
from storage.table import Table
from web.session import Session


class ShareTable(Table):
    def name(self) -> str:
        return "share"

    def columns(self) -> list[str]:
        return [
            "share_id TEXT PRIMARY KEY",
            "file_id TEXT NOT NULL",
            "creator_id TEXT NOT NULL",
            "password TEXT",
        ]

    def check_share_id(self, share_id: str) -> bool:
        """Checks if a share id has already been registered

        Args:
            share_id (str): The share ID to search for

        Returns:
            bool: Whether this ID has been taken
        """

        files = self.select("*", "share_id = ?", (share_id,))

        return len(files) > 0

    def _make_share_id(self) -> str:
        """Creates a new share id

        Returns:
            str: The new share id
        """

        # Create new file ID
        file_id = f"s{uuid4().hex}"

        # Keep on creating until we have one that does not exist
        while self.check_share_id(file_id):
            file_id = f"s{uuid4().hex}"

        return file_id

    def create_share(
        self, session: Session, file_id: str, password: Optional[str]
    ) -> str:
        """Creates a new share

        Args:
            session (Session): The session of the current user
            file_id (str): The ID of the file to share
            password (str): The password for the share

        Returns:
            str: The ID of the file
        """

        share_id = self._make_share_id()

        self.insert(
            share_id=share_id,
            file_id=file_id,
            creator_id=session.userid,
            password=password,
        )

        return share_id

    def can_download(self, share_id: str, password: Optional[str]) -> bool:
        """Checks if the share can be downloaded with the provided password

        Args:
            share_id (str): The ID of the share to check
            password (Optional[str]): The password

        Returns:
            bool: Whether this shared file can be downloaded
        """

        shares = self.select("password", "share_id = ?", (share_id,))

        return len(shares) > 0 and shares[0][0] == password

    def get_file_id(self, share_id: str) -> str:
        """Retrieves the file ID from a share ID

        Args:
            share_id (str): The share ID to check

        Returns:
            str: The file ID
        """

        shares = self.select("file_id", "share_id = ?", (share_id,))

        return shares[0][0]

    def has_password(self, share_id: str) -> bool:

        shares = self.select("password", "share_id = ?", (share_id,))

        return shares[0][0] != None
