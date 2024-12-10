from uuid import uuid4
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

    def make_file(self, user_session: Session, parent_dir: str, file_name: str) -> str:
        # Create new file ID
        file_id = uuid4().hex

        # Keep on creating until we have one that does not exist
        while self.check_file_id(file_id):
            file_id = uuid4().hex

        # Create file entry inside datadb
        self.insert(
            file_id=file_id,
            user_id=user_session.userid,
            file_type=0,
            file_location=parent_dir,
            file_name=file_name,
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
        self.update("file_name = ?", "file_id = ?", (new_name, file_id))

    def move(self, file_id: str, new_folder: str) -> None:
        self.update("file_location = ?", "file_id = ?", (new_folder, file_id))

    def delete_file(self, file_id: str) -> None:
        self.delete("file_id = ?", (file_id,))
