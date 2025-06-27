# Project : pytest-textualize
# File Name : helpers.py
# Dir Path : src/pytest_textualize
from __future__ import annotations

import os
from enum import Enum
from typing import Any
from typing import NoReturn
from typing import Protocol
from typing import TYPE_CHECKING
from typing import TypeGuard
from typing import TypeVar
from typing import get_args

if TYPE_CHECKING:
    from pytest_textualize.typist import ListStr


def get_bool_opt(opt_name: str, string: str) -> bool:
    if isinstance(string, bool):
        return string
    elif isinstance(string, int):
        return bool(string)
    elif not isinstance(string, str):
        raise ValueError(
            f"Invalid type {string!r} for option {opt_name}; use " "1/0, yes/no, true/false, on/off"
        )
    elif string.lower() in ("1", "yes", "true", "on"):
        return True
    elif string.lower() in ("0", "no", "false", "off"):
        return False
    else:
        raise ValueError(
            f"Invalid value {string!r} for option {opt_name}; use "
            "1/0, yes/no, true/false, on/off"
        )


def get_int_opt(opt_name: str, string: str) -> int:
    """As :func:`get_bool_opt`, but interpret the value as an integer."""
    try:
        return int(string)
    except TypeError:
        raise ValueError(
            f"Invalid type {string!r} for option {opt_name}; you " "must give an integer value"
        )
    except ValueError:
        raise ValueError(
            f"Invalid value {string!r} for option {opt_name}; you " "must give an integer value"
        )


def get_list_opt(opt_name: str, string: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(string, str):
        return string.split()
    elif isinstance(string, (list, tuple)):
        return list(string)
    else:
        raise ValueError(
            f"Invalid type {string!r} for option {opt_name}; you " "must give a list value"
        )


def literal_to_list(literal: Any) -> list[None | bool | bytes | int | str | Enum]:
    """
    Convert a typing.Literal into a list.

    Examples:
        >>> from typing import Literal
        >>> literal_to_list(Literal['a', 'b', 'c'])
        ['a', 'b', 'c']

        >>> literal_to_list(Literal['a', 'b', Literal['c', 'd', Literal['e']]])
        ['a', 'b', 'c', 'd', 'e']

        >>> literal_to_list(Literal['a', 'b', Literal[1, 2, Literal[None]]])
        ['a', 'b', 1, 2, None]
    """
    result = []

    for arg in get_args(literal):
        if arg is None or isinstance(arg, (bool, bytes, int, str, Enum)):
            result.append(arg)
        else:
            result.extend(literal_to_list(arg))

    return result


def is_list_of_strings(obj: object) -> TypeGuard[ListStr]:
    return isinstance(obj, list) and all(isinstance(item, str) for item in obj)

class SetEnv:
    """
    This class was taken from https://github.com/pydantic/pydantic-settings
    """

    def __init__(self) -> None:
        self.envars: set[Any] = set()

    def set(self, name: str, value: Any) -> None:
        self.envars.add(name)
        os.environ[name] = value

    def pop(self, name: str) -> None:
        self.envars.remove(name)
        os.environ.pop(name)

    def clear(self) -> None:
        for n in self.envars:
            os.environ.pop(n)
