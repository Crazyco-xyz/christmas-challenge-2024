class ProtocolError(RuntimeError):
    def __init__(self, *args) -> None:
        """The error to be thrown upon encountering any protocol related error

        Args:
            text (str): A short description of what went wrong
        """

        super().__init__(*args)
