import abc
from web.request import WebRequest
from web.response import WebResponse


class WebHandler(abc.ABC):
    def __init__(self, request: WebRequest) -> None:
        self._request = request

    @abc.abstractmethod
    def can_handle(self) -> bool:
        pass

    @abc.abstractmethod
    def handle(self, response: WebResponse) -> None:
        pass
