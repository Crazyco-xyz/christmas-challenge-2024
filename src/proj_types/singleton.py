from typing import Callable, Type, TypeVar


_T = TypeVar("_T")


def singleton(cls: Type[_T]) -> Callable[..., _T]:

    instances: dict[type, _T] = {}

    def get_instance(*args, **kwargs) -> _T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
