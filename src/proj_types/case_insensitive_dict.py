from typing import Optional


class CaseInsensitiveDict[_T]:
    def __init__(self, original: Optional[dict[str, _T]] = None) -> None:
        if original:
            self._data: dict[str, _T] = {k.lower(): v for k, v in original.items()}
        else:
            self._data: dict[str, _T] = {}

    def __setitem__(self, name: str, value: _T) -> None:
        self._data[name.lower()] = value

    def __getitem__(self, name: str) -> _T:
        return self._data[name.lower()]

    def __delitem__(self, name: str) -> None:
        del self._data[name.lower()]

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._data

    def get(self, name: str, default: _T) -> _T:
        return self._data.get(name.lower(), default)
