import os
from uuid import uuid4
import constants
from proj_types import file_type
from proj_types.file_type import FileType
from storage.table import Table
from web.session import Session


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

    def check_file_id(self, file_id: str) -> bool:
        """Checks if a file id has already been registered

        Args:
            file_id (str): The file ID to search for

        Returns:
            bool: Whether this ID has been taken
        """

        files = self.select("*", "file_id = ?", (file_id,))

        return len(files) > 0

    def check_folder_id(self, folder_id: str) -> bool:
        """Checks if the file id has already been registered and the file in its position is a folder

        Args:
            folder_id (str): The file_id of the folder

        Returns:
            bool: Whether the file is a folder
        """

        folders = self.select(
            "*", "file_id = ? AND file_type = ?", (folder_id, FileType.FOLDER.value)
        )

        return len(folders) > 0

    def _make_file_id(self) -> str:
        """Creates a new file id

        Returns:
            str: The new file id
        """

        # Create new file ID
        file_id = uuid4().hex

        # Keep on creating until we have one that does not exist
        while self.check_file_id(file_id):
            file_id = uuid4().hex

        return file_id

    def make_file(self, user_session: Session, parent_dir: str, file_name: str) -> str:
        """Creates an entry for a new file inside the database

        Args:
            user_session (Session): The user creating the file
            parent_dir (str): The parent directory of the file
            file_name (str): The name of the file

        Returns:
            str: The file_id of the created file
        """

        # Create new file ID
        file_id = self._make_file_id()

        # Create file entry inside datadb
        self.insert(
            file_id=file_id,
            user_id=user_session.userid,
            file_type=FileType.FILE.value,
            file_location=parent_dir,
            file_name=file_name,
        )

        return file_id

    def make_folder(
        self, user_session: Session, parent_dir: str, folder_name: str
    ) -> str:

        # Create new file ID
        file_id = self._make_file_id()

        self.insert(
            file_id=file_id,
            user_id=user_session.userid,
            file_type=FileType.FOLDER.value,
            file_location=parent_dir,
            file_name=folder_name,
        )

        return file_id

    def can_download(self, user_session: Session, file_id: str) -> bool:
        """Checks if the user can download the requested file

        Args:
            user_session (Session): The session of the user requesting the file
            file_id (str): The id of the file being requested

        Returns:
            bool: Whether the user can download the file
        """

        files = self.select(
            "*", "file_id = ? AND user_id = ?", (file_id, user_session.userid)
        )

        return len(files) > 0

    def get_name(self, file_id: str) -> str:
        """Retrieves the name of the file

        Args:
            file_id (str): The ID of the file

        Returns:
            str: The name of the file
        """

        names = self.select("file_name", "file_id = ?", (file_id,))

        if len(names) == 0:
            return ""

        return names[0][0]

    def rename(self, file_id: str, new_name: str) -> None:
        """Renames the file file_id to new_name

        Args:
            file_id (str): The file to rename
            new_name (str): The new name of the file
        """

        self.update("file_name = ?", "file_id = ?", (new_name, file_id))

    def move(self, file_id: str, new_folder: str) -> None:
        """Moves the file file_id into new_folder

        Args:
            file_id (str): The file to move
            new_folder (str): The new parent directory of the file
        """

        self.update("file_location = ?", "file_id = ?", (new_folder, file_id))

    def delete_file(self, file_id: str) -> None:
        """Deletes the file stored at file_id or deletes
        all files in the folder stored at file_id

        Args:
            file_id (str): The file to delete
        """

        if self.check_folder_id(file_id):
            # Delete all files in folder
            files = self.select("file_id", "file_location = ?", (file_id,))

            for f in files:
                self.delete_file(f[0])
        else:
            # Delete the file on the HDD
            os.remove(os.path.join(constants.FILES, file_id))

        # Delete the file from the table
        self.delete("file_id = ?", (file_id,))

    def name_check(self, session: Session, parent_dir: str, file_name: str) -> bool:
        """Checks if a file with the given name already exists in the given directory

        Args:
            session (Session): The user to perform the check for
            parent_dir (str): The id of the directory to perform the check in
            file_name (str): The file name to search for

        Returns:
            bool: Whether the new file can be created without conflicts
        """

        files = self.select(
            "*",
            "user_id = ? AND file_location = ? AND file_name = ?",
            (session.userid, parent_dir, file_name),
        )

        return len(files) == 0
