class ProtocolError(RuntimeError):
    def __init__(self, text: str) -> None:
        """The error to be thrown upon encountering any protocol related error

        Args:
            text (str): A short description of what went wrong
        """

        super().__init__()

        self._text = text

    @property
    def desc(self) -> str:
        """
        Returns:
            str: A short description of what went wrong
        """

        return self._text
