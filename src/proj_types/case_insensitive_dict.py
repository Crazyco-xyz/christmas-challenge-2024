from typing import Optional


class CaseInsensitiveDict[_T]:
    def __init__(self, original: Optional[dict[str, _T]] = None) -> None:
        if original:
            self._data: dict[str, _T] = {k.lower(): v for k, v in original.items()}
        else:
            self._data: dict[str, _T] = {}

    def __setitem__(self, name: str, value: _T) -> None:
        """Set the value of a key in the dictionary

        Args:
            name (str): The key to set the value of
            value (_T): The value to set the key to
        """

        self._data[name.lower()] = value

    def __getitem__(self, name: str) -> _T:
        """Get the value of a key in the dictionary

        Args:
            name (str): The key to get the value of

        Returns:
            _T: The value of the key
        """

        return self._data[name.lower()]

    def __delitem__(self, name: str) -> None:
        """Delete a key from the dictionary

        Args:
            name (str): The key to delete
        """

        del self._data[name.lower()]

    def __contains__(self, name: str) -> bool:
        """Check if a key is in the dictionary

        Args:
            name (str): The key to check for

        Returns:
            bool: Whether the key is in the dictionary
        """

        return name.lower() in self._data

    def get(self, name: str, default: _T) -> _T:
        """Get the value of a key in the dictionary, with a default value if the key is not present

        Args:
            name (str): The key to get the value of
            default (_T): The default value to return if the key is not present

        Returns:
            _T: The value of the key, or the default value if the key is not present
        """

        return self._data.get(name.lower(), default)
